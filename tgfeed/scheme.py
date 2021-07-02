from dataclasses import dataclass, field

from telethon.tl.types import Channel as TGChannel


@dataclass
class Chat:
    forwarded_offset: int = 0


@dataclass
class Feed:
    tg_channel: TGChannel
    chats: dict[int, Chat] = field(default_factory=dict)
