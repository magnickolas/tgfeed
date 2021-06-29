from dataclasses import dataclass

@dataclass
class Feed:
    name: str
    chats_posts_ids_latest: dict[int, int]
