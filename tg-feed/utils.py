from typing import Callable, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")

def map_optional(f: Callable[[T], U], x: Optional[T]) -> Optional[U]:
    return x if x is None else f(x)
