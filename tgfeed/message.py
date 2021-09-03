from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import groupby

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


def remove_message_headers(messages: list[Message]) -> list[AbstractMessage]:
    transformed_messages = list[AbstractMessage]()
    for grouped_id, grouped_messages in groupby(messages, lambda x: x.grouped_id):
        if grouped_id is None:
            transformed_messages.extend(
                map(
                    SimpleMessage,
                    filter(
                        lambda x: getattr(x, "message", None) is not None,
                        grouped_messages,
                    ),
                )
            )
        else:
            transformed_messages.append(GroupedMessage(list(grouped_messages)))
    return transformed_messages
