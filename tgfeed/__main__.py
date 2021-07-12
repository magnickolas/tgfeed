import shelve
from asyncio import sleep
from datetime import datetime
from itertools import chain
from pathlib import Path

from loguru import logger
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import Channel, Message, TypeDialogFilter, TypeInputPeer, Updates

from tgfeed import config
from tgfeed.scheme import ChatInfo, Feed


async def create_feed(feed_title: str) -> Feed:
    logger.info(f"creating a new feed channel '{feed_title}'")
    create_channel_updates: Updates = await client(
        CreateChannelRequest(feed_title, "")
    )  # type: ignore
    return Feed(tg_channel=create_channel_updates.chats[0])  # type: ignore


async def get_new_chat_messages(
    chat_info: ChatInfo, peer: TypeInputPeer
) -> list[Message]:
    limit = None if chat_info.forwarded_offset else config.INITIAL_FORWARD_CHAT_LIMIT
    chat_messages = await client.get_messages(
        peer, limit=limit, min_id=chat_info.forwarded_offset
    )
    if chat_messages:
        chat_info.forwarded_offset = max(map(lambda x: x.id, chat_messages))
    return chat_messages


async def forward_messages_to_channel(
    messages: list[Message], channel: Channel
) -> None:
    messages = sorted(messages, key=lambda x: x.date or datetime.now())
    await client.forward_messages(channel, messages)


async def update_feeds(title_to_feed: dict[str, Feed]) -> None:
    subscribed_dialogs = []
    async for dialog in client.iter_dialogs():
        subscribed_dialogs.append(dialog.input_entity)
    dialog_filter: TypeDialogFilter
    for dialog_filter in await client(GetDialogFiltersRequest()):
        if dialog_filter.title.startswith(config.FOLDER_FEED_PREFIX):
            feed_title = dialog_filter.title.removeprefix(config.FOLDER_FEED_PREFIX)
            if feed_title not in title_to_feed:
                title_to_feed[feed_title] = await create_feed(feed_title)
            feed = title_to_feed[feed_title]
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
            await forward_messages_to_channel(messages, channel)


async def main() -> None:
    (db_dir := Path(config.DB_DIR)).mkdir(exist_ok=True)
    db_path = str(db_dir / "data")
    while True:
        logger.info("updating feed...")
        with shelve.open(db_path, writeback=True) as shelf:
            shelf.setdefault("feeds", dict[str, Feed]())
            await update_feeds(shelf["feeds"])
        await sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    client = TelegramClient("tgfeed", config.APP_ID, config.APP_HASH)
    client.start()

    with client:
        client.loop.run_until_complete(main())
