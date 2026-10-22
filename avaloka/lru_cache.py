"""Problem 1: LRU cache with O(1) get and put.

Design: a hash map gives O(1) lookup from key to node, and a doubly linked
list keeps the nodes in recency order (most recent next to the head, least
recent next to the tail). Two sentinel nodes mean the list is never empty,
so insert and unlink have no edge cases.
"""

from __future__ import annotations

import threading
from typing import Generic, Hashable, Iterator, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

MISSING = -1  # value returned by get() for an absent key, as the spec requires


class _Node(Generic[K, V]):
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: Optional[K] = None, value: Optional[V] = None) -> None:
        self.key = key
        self.value = value
        self.prev: Optional[_Node[K, V]] = None
        self.next: Optional[_Node[K, V]] = None


class LRUCache(Generic[K, V]):
    """Fixed-capacity Least Recently Used cache.

    get(key)        -> value, or -1 if absent. Marks the key as most recently used.
    put(key, value) -> inserts or updates. Evicts the least recently used key
                       first if a new key would exceed capacity.

    Both operations are O(1) time. Space is O(capacity).
    """

    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an int")
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._map: dict[K, _Node[K, V]] = {}
        # Sentinels: head.next is the most recently used, tail.prev the least.
        self._head: _Node[K, V] = _Node()
        self._tail: _Node[K, V] = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    # ---- linked-list primitives, each O(1) ---------------------------------

    def _unlink(self, node: _Node[K, V]) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _push_front(self, node: _Node[K, V]) -> None:
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _move_to_front(self, node: _Node[K, V]) -> None:
        if self._head.next is not node:
            self._unlink(node)
            self._push_front(node)

    # ---- public API --------------------------------------------------------

    def get(self, key: K) -> V | int:
        node = self._map.get(key)
        if node is None:
            return MISSING
        self._move_to_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        node = self._map.get(key)
        if node is not None:
            # Updating an existing key never evicts; it just refreshes recency.
            node.value = value
            self._move_to_front(node)
            return
        if len(self._map) >= self.capacity:
            lru = self._tail.prev
            self._unlink(lru)
            del self._map[lru.key]
        node = _Node(key, value)
        self._map[key] = node
        self._push_front(node)

    # ---- read-only helpers (do NOT change recency) -------------------------

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: object) -> bool:
        return key in self._map

    def keys_mru_to_lru(self) -> list[K]:
        """Keys from most to least recently used. O(n); for debugging/tests."""
        return [node.key for node in self._iter_nodes()]

    def _iter_nodes(self) -> Iterator[_Node[K, V]]:
        node = self._head.next
        while node is not self._tail:
            yield node
            node = node.next

    def _check_invariants(self) -> None:
        """Assert the map and the list describe the same set of entries."""
        forward = list(self._iter_nodes())
        backward = []
        node = self._tail.prev
        while node is not self._head:
            backward.append(node)
            node = node.prev
        assert forward == backward[::-1], "prev/next pointers disagree"
        assert len(forward) == len(self._map) <= self.capacity, "size mismatch"
        for n in forward:
            assert self._map[n.key] is n, "map points at a different node"

    def __repr__(self) -> str:
        items = ", ".join(f"{n.key!r}: {n.value!r}" for n in self._iter_nodes())
        return f"LRUCache(capacity={self.capacity}, MRU->LRU {{{items}}})"


class ThreadSafeLRUCache(LRUCache[K, V]):
    """LRUCache guarded by a single mutex.

    get() is not read-only (it reorders the list), so a reader/writer lock
    would not help: every operation is a write. One lock around each public
    method makes get/put atomic with respect to each other.
    """

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._lock = threading.Lock()

    def get(self, key: K) -> V | int:
        with self._lock:
            return super().get(key)

    def put(self, key: K, value: V) -> None:
        with self._lock:
            super().put(key, value)

    def __len__(self) -> int:
        with self._lock:
            return super().__len__()

    def __contains__(self, key: object) -> bool:
        with self._lock:
            return super().__contains__(key)

    def keys_mru_to_lru(self) -> list[K]:
        with self._lock:
            return super().keys_mru_to_lru()
