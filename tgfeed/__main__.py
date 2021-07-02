import shelve
from asyncio import sleep
from itertools import chain
from pathlib import Path

from loguru import logger
from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import Channel, Updates

from tgfeed import config
from tgfeed.scheme import Chat, Feed


async def update_feeds(feeds: dict[str, Feed], client: TelegramClient) -> None:
    for dialog_filter in await client(GetDialogFiltersRequest()):
        if dialog_filter.title.startswith(config.FOLDER_FEED_PREFIX):
            feed_title = dialog_filter.title.removeprefix(config.FOLDER_FEED_PREFIX)
            if feed_title not in feeds:
                logger.info(f"create new feed channel '{feed_title}'")
                create_channel_updates: Updates = await client(
                    CreateChannelRequest(feed_title, "")
                )  # type: ignore
                channel: Channel = create_channel_updates.chats[0]  # type: ignore
                feed = feeds[feed_title] = Feed(tg_channel=channel)
            else:
                feed = feeds[feed_title]
                channel = feed.tg_channel
            messages = []
            for tg_chat in chain(
                dialog_filter.pinned_peers, dialog_filter.include_peers
            ):
                chat = feed.chats.setdefault(tg_chat.access_hash, Chat())
                limit = (
                    None if chat.forwarded_offset else config.INITIAL_FORWARD_CHAT_LIMIT
                )
                chat_messages = []
                async for message in client.iter_messages(
                    tg_chat, limit=limit, min_id=chat.forwarded_offset
                ):
                    chat_messages.append(message)
                if chat_messages:
                    chat.forwarded_offset = max(map(lambda x: x.id, chat_messages))
                messages += chat_messages
            messages.sort(key=lambda x: x.date)
            await client.forward_messages(channel, messages)


async def main(client: TelegramClient) -> None:
    db_dir = Path(config.DB_DIR)
    db_dir.mkdir(exist_ok=True)
    db_path = str(db_dir / "data")
    while True:
        logger.info("updating feed...")
        with shelve.open(db_path, writeback=True) as shelf:
            shelf.setdefault("feeds", dict[str, Feed]())
            await update_feeds(shelf["feeds"], client)
        await sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    api_id = config.APP_ID
    api_hash = config.APP_HASH
    client = TelegramClient("tgfeed", api_id, api_hash)
    client.start()

    with client:
        client.loop.run_until_complete(main(client))
