"""Metadata stored alongside every cached value."""
from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class CacheObject:
    key: str
    value: Any
    size: int
    cost: float
    frequency: int = 1
    created_at: float = field(default_factory=time)
    last_accessed: float = field(default_factory=time)

    def touch(self) -> None:
        """Record an access to this object."""
        self.frequency += 1
        self.last_accessed = time()
