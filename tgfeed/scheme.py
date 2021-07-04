from dataclasses import dataclass, field

from telethon.tl.types import Channel as TGChannel


@dataclass
class ChatInfo:
    forwarded_offset: int = 0


@dataclass
class Feed:
    tg_channel: TGChannel
    hash_to_chat_info: dict[int, ChatInfo] = field(default_factory=dict)
