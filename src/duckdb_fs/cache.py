"""Small bounded LRU used for pure virtual-directory listings."""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class BoundedLRU(Generic[K, V]):
    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("cache capacity cannot be negative")
        self.capacity = capacity
        self._values: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> V | None:
        try:
            value = self._values.pop(key)
        except KeyError:
            return None
        self._values[key] = value
        return value

    def put(self, key: K, value: V) -> None:
        if self.capacity == 0:
            return
        self._values[key] = value
        self._values.move_to_end(key)
        while len(self._values) > self.capacity:
            self._values.popitem(last=False)
