from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from telethon import TelegramClient
from telethon.hints import EntityLike
from telethon.tl.types import Message


class AbstractMessage(ABC):
    @abstractmethod
    async def send(self, client: TelegramClient, entity: EntityLike):
        ...


@dataclass
class SimpleMessage(AbstractMessage):
    message: Message

    async def send(self, client: TelegramClient, entity: EntityLike):
        await client.send_message(entity, self.message)


@dataclass
class GroupedMessage(AbstractMessage):
    messages: list[Message] = field(default_factory=list)

    async def send(self, client: TelegramClient, entity: EntityLike):
        caption = ""
        for msg in self.messages:
            if msg.message:
                caption = msg.message
                break
        await client.send_file(
            entity, file=self.messages, caption=caption  # type: ignore
        )
