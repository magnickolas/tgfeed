import shelve
from telethon import TelegramClient#, events, sync
from telethon.tl.functions import channels, messages
from . import config
from pathlib import Path
from .scheme import Feed

async def main(client) -> None:
    db_dir = Path(config.DB_DIR)
    db_dir.mkdir(exist_ok=True)
    db_path = str(db_dir / "data.db")
        
    with shelve.open(db_path) as shelf:
        def init(key, init_value):
            if key not in shelf:
                shelf[key] = init_value
        init("feeds", [])

if __name__ == "__main__":
    api_id   = config.APP_ID
    api_hash = config.APP_HASH
    client = TelegramClient("session_name", api_id, api_hash)
    client.start()

    with client:
        client.loop.run_until_complete(main(client))
