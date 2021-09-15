import os
from typing import Callable, Optional, TypeVar, overload

from appdirs import user_data_dir

T = TypeVar("T")


def str_to_bool(x: str) -> bool:
    if x.lower() in ("true", "t", "1", "y", "yes"):
        return True
    elif x.lower() in ("false", "f", "0", "n", "no"):
        return False
    raise ValueError(f"Cannot cast `{x}` to bool")


@overload
def __get(name, *, value_type: Callable[[str], T], default: T) -> T:
    ...


@overload
def __get(name, *, value_type: Callable[[str], T], default=None) -> Optional[T]:
    ...


def __get(name, *, value_type, default=None):
    env_var = os.environ.get(name)
    if env_var is None:
        return default
    else:
        if value_type is bool:
            return str_to_bool(env_var)
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
FOLDER_FEED_PREFIX: str = __get("FOLDER_FEED_PREFIX", value_type=str, default="*")
# Directory to store info about feeds and chats
DB_DIR: str = __get("DB_DIR", value_type=str, default=user_data_dir("tgfeed"))
# How many messages to take from a new chat to forward to the feed
INITIAL_FORWARD_CHAT_LIMIT: int = __get(
    "INITIAL_FORWARD_CHAT_LIMIT", value_type=int, default=1
)
# Polling interval in seconds
POLL_INTERVAL: int = __get("POLL_INTERVAL", value_type=int, default=5)
# Whether to use existing channel with the approptiate name to forward to
USE_EXISTING_CHANNEL: bool = __get(
    "USE_EXISTING_CHANNEL", value_type=bool, default=False
)
# Ignore duplicate posts from channels
IGNORE_DUPLICATE_POSTS: bool = __get(
    "IGNORE_DUPLICATE_POSTS", value_type=bool, default=True
)
# Remove forwarded header from posts
REMOVE_FORWARDED_HEADER: bool = __get(
    "REMOVE_FORWARDED_HEADER", value_type=bool, default=False
)
# Mark channels as read after forwarding
MARK_CHANNELS_AS_READ: bool = __get(
    "MARK_CHANNELS_AS_READ", value_type=bool, default=True
)
# Ignore messages with potential advertisement
IGNORE_ADVERTISEMENT: bool = __get(
    "IGNORE_ADVERTISEMENT", value_type=bool, default=False
)
