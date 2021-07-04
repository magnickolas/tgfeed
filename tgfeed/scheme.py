from dataclasses import dataclass, field

from telethon.tl.types import Channel as TGChannel
from telethon.tl.types import TypeInputPeer


@dataclass
class ChatInfo:
    forwarded_offset: int = 0


@dataclass
class Feed:
    tg_channel: TGChannel
    peer_to_chat_info: dict[TypeInputPeer, ChatInfo] = field(default_factory=dict)
