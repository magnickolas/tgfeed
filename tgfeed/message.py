from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import groupby

from loguru import logger
from telethon import TelegramClient
from telethon.hints import EntityLike
from telethon.tl.types import Message


class AbstractMessage(ABC):
    @abstractmethod
    async def send(self, client: TelegramClient, entity: EntityLike): ...

    @abstractmethod
    def get_caption(self) -> str: ...

    @abstractmethod
    def has_media(self) -> bool: ...


@dataclass
class SimpleMessage(AbstractMessage):
    message: Message

    async def send(self, client: TelegramClient, entity: EntityLike):
        try:
            await client.send_message(entity, self.message)
        except Exception as e:
            logger.debug(
                f"Failed to send message {self.message.id}, trying to forward: {e}"
            )
            try:
                await client.forward_messages(entity, self.message)
            except Exception as e:
                logger.warning(
                    f"Skipping message that can't be forwarded: {self.message.id} - {e}"
                )
                return

    def get_caption(self) -> str:
        return self.message.text

    def has_media(self) -> bool:
        return self.message.media is not None


@dataclass
class GroupedMessage(AbstractMessage):
    messages: list[Message] = field(default_factory=list)

    async def send(self, client: TelegramClient, entity: EntityLike):
        try:
            await client.send_file(
                entity, file=self.messages, caption=self.get_caption()
            )
        except Exception as e:
            message_ids = [msg.id for msg in self.messages]
            logger.warning(f"Skipping grouped message {message_ids} due to error: {e}")
            return

    def get_caption(self) -> str:
        caption = ""
        for msg in self.messages:
            if msg.message:
                caption = msg.text
                break
        return caption

    def has_media(self) -> bool:
        return True


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
