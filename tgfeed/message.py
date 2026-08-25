from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import groupby

from loguru import logger
from telethon import TelegramClient
from telethon.hints import EntityLike
from telethon.tl import types
from telethon.tl.types import Message


class AbstractMessage(ABC):
    @abstractmethod
    async def send(self, client: TelegramClient, entity: EntityLike): ...

    @abstractmethod
    def get_caption(self) -> str: ...

    @abstractmethod
    def set_caption(self, caption: str) -> None: ...

    @abstractmethod
    def get_advertisement_text(self) -> str: ...

    @abstractmethod
    def has_media(self) -> bool: ...


@dataclass
class SimpleMessage(AbstractMessage):
    message: Message
    caption_modified: bool = field(default=False, init=False)

    async def send(self, client: TelegramClient, entity: EntityLike):
        if (
            isinstance(self.message.media, types.MessageMediaPoll)
            and self.message.media.poll.quiz
        ):
            await self.send_quiz(client, entity, self.message.media)
            return
        try:
            await client.send_message(entity, self.message)
        except Exception as e:
            if self.caption_modified:
                logger.warning(
                    "Skipping message that can't be sent with its replaced caption: "
                    f"{self.message.id} - {e}"
                )
                return
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

    async def send_quiz(
        self,
        client: TelegramClient,
        entity: EntityLike,
        media: types.MessageMediaPoll,
    ) -> None:
        correct_options = {
            result.option for result in (media.results.results or []) if result.correct
        }
        correct_answers = [
            index
            for index, answer in enumerate(media.poll.answers)
            if answer.option in correct_options
        ]
        if not correct_answers:
            logger.warning(
                f"Skipping quiz {self.message.id}: its correct answer is unavailable"
            )
            return
        try:
            await client.send_file(
                entity,
                types.InputMediaPoll(
                    poll=media.poll,
                    correct_answers=correct_answers,
                    solution=media.results.solution,
                    solution_entities=media.results.solution_entities,
                ),
                caption=self.message.message or "",
                silent=self.message.silent,
                formatting_entities=self.message.entities,
                parse_mode=None,
            )
        except Exception as error:
            logger.warning(
                f"Skipping quiz {self.message.id} that can't be recreated: {error}"
            )

    def get_caption(self) -> str:
        return self.message.message or ""

    def set_caption(self, caption: str) -> None:
        self.message.text = caption
        self.caption_modified = True

    def get_advertisement_text(self) -> str:
        return "\n".join((self.get_caption(), *_get_button_urls(self.message)))

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
                caption = msg.message
                break
        return caption

    def set_caption(self, caption: str) -> None:
        for msg in self.messages:
            if msg.message:
                msg.text = caption
                break

    def get_advertisement_text(self) -> str:
        button_urls = [
            url for message in self.messages for url in _get_button_urls(message)
        ]
        return "\n".join((self.get_caption(), *button_urls))

    def has_media(self) -> bool:
        return True


def _get_button_urls(message: Message) -> list[str]:
    reply_markup = message.reply_markup
    if reply_markup is None:
        return []
    return [
        button.url
        for row in reply_markup.rows
        for button in row.buttons
        if isinstance(getattr(button, "url", None), str)
    ]


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
