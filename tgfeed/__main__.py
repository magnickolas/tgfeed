import json
from asyncio import sleep
from datetime import datetime
from itertools import chain
from pathlib import Path

import jsonpickle
from loguru import logger
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, ReadHistoryRequest
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import (
    Channel,
    Message,
    PeerChannel,
    TypeDialogFilter,
    TypeInputPeer,
    Updates,
)

from tgfeed import config
from tgfeed.message import remove_message_headers
from tgfeed.scheme import ChatInfo, Feed
from tgfeed.utils import open_atomic
from tgfeed.validate import is_potential_advertisement


async def create_feed(feed_title: str) -> Feed:
    if config.USE_EXISTING_CHANNEL:
        async for dialog in client.iter_dialogs():
            if dialog.name == feed_title:
                return Feed(tg_channel=dialog.entity)
    logger.info(f"creating a new feed channel '{feed_title}'")
    create_channel_updates: Updates = await client(
        CreateChannelRequest(feed_title, "")
    )  # type: ignore
    return Feed(tg_channel=create_channel_updates.chats[0])  # type: ignore


async def get_new_chat_messages(
    chat_info: ChatInfo, peer: TypeInputPeer
) -> list[Message]:
    is_initial_forward = chat_info.forwarded_offset == 0
    limit = max(1, config.INITIAL_FORWARD_CHAT_LIMIT) if is_initial_forward else None
    chat_messages = (
        await client.get_messages(peer, limit=limit, min_id=chat_info.forwarded_offset)
    )[::-1]
    if chat_messages:
        chat_info.forwarded_offset = max(map(lambda x: x.id, chat_messages))
    if is_initial_forward:
        chat_messages = chat_messages[: config.INITIAL_FORWARD_CHAT_LIMIT]
    return chat_messages


async def mark_chat_as_read(peer: TypeInputPeer) -> None:
    await client(ReadHistoryRequest(peer, 0))  # type: ignore


async def forward_messages_to_channel(
    messages: list[Message], channel: Channel
) -> None:
    messages = sorted(messages, key=lambda x: x.date or datetime.now())
    if config.REMOVE_FORWARDED_HEADER:
        transformed_messages = remove_message_headers(messages)
        for message in transformed_messages:
            print(getattr(message, "message"))
            if config.IGNORE_ADVERTISEMENT and is_potential_advertisement(
                message.get_caption()
            ):
                continue
            await message.send(client, channel)
    else:
        await client.forward_messages(channel, messages)


def deduplicate_feed_messages(messages: list[Message], feed: Feed) -> list[Message]:
    deduplicated_messages = []
    for message in messages:
        if message.fwd_from is None:
            post_id = message.id
            peer_from = message.peer_id
            if post_id is not None and isinstance(peer_from, PeerChannel):
                chan_id = peer_from.channel_id
                post = (chan_id, post_id)
                if post not in feed.sent_posts_ids:
                    feed.sent_posts_ids.add(post)
                    deduplicated_messages.append(message)
        else:
            post_id = message.fwd_from.channel_post
            peer_from = message.fwd_from.from_id
            if post_id is not None and isinstance(peer_from, PeerChannel):
                chan_id = peer_from.channel_id
                post = (chan_id, post_id)
                if post not in feed.sent_posts_ids:
                    feed.sent_posts_ids.add(post)
                    deduplicated_messages.append(message)
            else:
                deduplicated_messages.append(message)
    return deduplicated_messages


async def update_feeds(title_to_feed: dict[str, str]) -> None:
    subscribed_dialogs = []
    async for dialog in client.iter_dialogs():
        subscribed_dialogs.append(dialog.input_entity)
    dialog_filter: TypeDialogFilter
    for dialog_filter in await client(GetDialogFiltersRequest()):
        if dialog_filter.title.startswith(config.FOLDER_FEED_PREFIX):
            feed_title = dialog_filter.title.removeprefix(config.FOLDER_FEED_PREFIX)
            if feed_title not in title_to_feed:
                feed = await create_feed(feed_title)
                title_to_feed[feed_title] = jsonpickle.encode(feed)  # type: ignore
            feed: Feed = jsonpickle.decode(title_to_feed[feed_title])  # type: ignore
            channel = feed.tg_channel
            messages = []
            peer: TypeInputPeer
            for peer in filter(
                lambda x: x in subscribed_dialogs,
                chain(dialog_filter.pinned_peers, dialog_filter.include_peers),
            ):
                chat_info = feed.peer_to_chat_info.setdefault(
                    peer.to_json() or peer.stringify(), ChatInfo()
                )
                messages += await get_new_chat_messages(chat_info, peer)
                if config.MARK_CHANNELS_AS_READ:
                    await mark_chat_as_read(peer)
            if config.IGNORE_DUPLICATE_POSTS:
                messages = deduplicate_feed_messages(messages, feed)
            title_to_feed[feed_title] = jsonpickle.encode(feed)  # type: ignore
            await forward_messages_to_channel(messages, channel)


async def main() -> None:
    (db_dir := Path(config.DB_DIR)).mkdir(exist_ok=True)
    db_path = db_dir / "data.db"
    while True:
        logger.info("updating feed...")
        if db_path.exists():
            db_json = json.load(open(db_path, "r"))
        else:
            db_json = dict()
        feeds = db_json.setdefault("feeds", dict[str, str]())
        await update_feeds(feeds)

        with open_atomic(db_path, "w") as f:
            json.dump(db_json, f)

        await sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    client = TelegramClient("tgfeed", config.APP_ID, config.APP_HASH)
    client.start()

    with client:
        client.loop.run_until_complete(main())
