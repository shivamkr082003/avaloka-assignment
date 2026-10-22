"""Problem 2: event scheduler.

Events are (start, end) tuples with start < end. An event that ends at time t
does not overlap one that starts at t, so intervals behave as half-open [start, end).
"""

from __future__ import annotations

import heapq
from typing import Iterable, Sequence

Event = tuple[float, float]


def _validate(events: Iterable[Event]) -> list[Event]:
    checked = []
    for i, ev in enumerate(events):
        try:
            start, end = ev
        except (TypeError, ValueError):
            raise ValueError(f"event #{i} {ev!r} is not a (start, end) pair") from None
        if not start < end:
            raise ValueError(f"event #{i} {ev!r} must have start < end")
        checked.append((start, end))
    return checked


def can_attend_all(events: Iterable[Event]) -> bool:
    """True if no two events overlap (back-to-back events are fine).

    Sort by start time; then any overlap must show up between neighbours,
    because if event i doesn't run past the start of event i+1, it can't run
    past the start of anything later either. O(n log n) time, O(n) space.
    """
    ordered = sorted(_validate(events))
    for (_, prev_end), (start, _) in zip(ordered, ordered[1:]):
        if start < prev_end:
            return False
    return True


def min_rooms_required(events: Iterable[Event]) -> int:
    """Minimum rooms so every event gets a room (max number running at once).

    Process events by start time and keep a min-heap of end times of the rooms
    currently in use. Before placing an event, free every room whose meeting
    has ended by the time this one starts (end <= start, the adjacency rule).
    The largest the heap ever gets is the answer. O(n log n) time, O(n) space.
    """
    ordered = sorted(_validate(events))
    busy_until: list[float] = []
    peak = 0
    for start, end in ordered:
        while busy_until and busy_until[0] <= start:
            heapq.heappop(busy_until)
        heapq.heappush(busy_until, end)
        peak = max(peak, len(busy_until))
    return peak


def min_rooms_sweep(events: Iterable[Event]) -> int:
    """Same answer as min_rooms_required, by a two-pointer sweep line.

    Sort starts and ends separately and walk through time. On a tie, the end
    is processed first, which is what makes back-to-back events share a room.
    Kept as an independent cross-check. O(n log n) time, O(n) space.
    """
    checked = _validate(events)
    starts = sorted(s for s, _ in checked)
    ends = sorted(e for _, e in checked)
    in_use = peak = 0
    j = 0
    for s in starts:
        while ends[j] <= s:  # every end <= s belongs to an earlier start, so j stays in range
            in_use -= 1
            j += 1
        in_use += 1
        peak = max(peak, in_use)
    return peak


def room_name(index: int) -> str:
    """0 -> 'Room A', 25 -> 'Room Z', 26 -> 'Room AA' (spreadsheet-style)."""
    if index < 0:
        raise ValueError("index must be non-negative")
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return f"Room {letters}"


def assign_rooms(events: Sequence[Event]) -> list[str]:
    """Give each event a named room, using the minimum number of rooms.

    Returns a list aligned with the input: result[i] is the room for events[i].
    Two heaps: `busy` holds (end_time, room) for rooms in use, `free` holds
    rooms that were opened earlier and are now empty. Taking the smallest free
    room keeps the output deterministic (Room A is always reused first).
    O(n log n) time, O(n) space.
    """
    checked = _validate(events)
    order = sorted(range(len(checked)), key=lambda i: checked[i])
    busy: list[tuple[float, int]] = []
    free: list[int] = []
    rooms_opened = 0
    result = [""] * len(checked)
    for i in order:
        start, end = checked[i]
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(free, room)
        if free:
            room = heapq.heappop(free)
        else:
            room = rooms_opened
            rooms_opened += 1
        heapq.heappush(busy, (end, room))
        result[i] = room_name(room)
    return result
