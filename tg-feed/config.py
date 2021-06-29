from appdirs import user_data_dir
import os
from typing import Callable, Optional, TypeVar
from .utils import map_optional

T = TypeVar("T")

def __get(name, *, value_type: Callable[[str], T] = str) -> Optional[T]:
    return map_optional(value_type, os.environ.get(name))

def __get_nonempty(name, *, value_type: Callable[[str], T] = str) -> T:
    res = __get(name, value_type=value_type)
    if res is None:
        raise ValueError(f"Argument {name} is not specified")
    if not res:
        raise ValueError(f"Argument {name} is empty")
    return res

# REQUIRED
APP_ID: int   = __get_nonempty("APP_ID", value_type=int)
APP_HASH: str = __get_nonempty("APP_HASH")

# OPTIONAL
FOLDER_FEED_PREFIX: str   = __get("FOLDER_FEED_PREFIX") or "*"
DB_DIR: str =  __get("DB_DIR") or user_data_dir("tg-feed", "magnickolas")
