import os
from typing import Callable, Optional, TypeVar

from appdirs import user_data_dir

T = TypeVar("T")


def __get(name, *, value_type: Callable[[str], T]) -> Optional[T]:
    env_var = os.environ.get(name)
    if env_var is None:
        return None
    else:
        return value_type(env_var)


def __get_nonempty(name, *, value_type: Callable[[str], T]) -> T:
    res = __get(name, value_type=value_type)
    if res is None:
        raise ValueError(f"Argument {name} is not specified")
    if not res:
        raise ValueError(f"Argument {name} is empty")
    return res


# ---REQUIRED--- #
# https://core.telegram.org/api/obtaining_api_id
APP_ID: int = __get_nonempty("APP_ID", value_type=int)
APP_HASH: str = __get_nonempty("APP_HASH", value_type=str)

# ---OPTIONAL--- #
# Only telegram folders starting with the specific prefix
# will be grouped into a channel
FOLDER_FEED_PREFIX: str = __get("FOLDER_FEED_PREFIX", value_type=str) or "*"
# Directory to store info about feeds and chats
DB_DIR: str = __get("DB_DIR", value_type=str) or user_data_dir("tgfeed")
# How many messages to take from a new chat to forward to the feed
INITIAL_FORWARD_CHAT_LIMIT: int = (
    __get("INITIAL_FORWARD_CHAT_LIMIT", value_type=int) or 10
)
# Polling interval in seconds
POLL_INTERVAL: int = __get("POLL_INTERVAL", value_type=int) or 5
