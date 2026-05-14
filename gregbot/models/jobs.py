from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    key: str
    name: str
    titles: tuple[str, ...]
    min_pay: int
    max_pay: int
    success_messages: tuple[str, ...]
    footers: tuple[str, ...]