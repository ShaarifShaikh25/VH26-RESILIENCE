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
    previous_accessed: float | None = None
    access_times: list[float] = field(default_factory=list)
    last_sequence: int = 0

    def __post_init__(self) -> None:
        if not self.access_times:
            self.access_times.append(self.created_at)

    def touch(self, seq: int = 0) -> None:
        """Record an access to this object."""
        now = time()
        self.frequency += 1
        self.previous_accessed = self.last_accessed
        self.last_accessed = now
        self.access_times.append(now)
        self.access_times = self.access_times[-100:]
        if seq > 0:
            self.last_sequence = seq
