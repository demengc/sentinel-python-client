from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    content: list[T]
    size: int
    number: int
    total_elements: int
    total_pages: int
