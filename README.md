# Avaloka take-home: LRU Cache & Event Scheduler

Shivam Kumar, for the AI / Multi-Agent Systems Intern role at Avaloka (Guruvai Sciences).

Pure Python 3.10+, standard library only. Nothing to install. The full write-up (approach, code and the four discussion answers) is in the PDF submitted by email; this repository contains the same code, runnable.

```bash
python3 demo.py                                   # examples from the assignment
python3 -m unittest discover -s tests -t . -v     # 27 tests
python3 -m benchmarks.bench                       # complexity + concurrency evidence
```

## What's here

| File | What it contains |
|---|---|
| `avaloka/lru_cache.py` | `LRUCache` (hash map + doubly linked list with sentinels, O(1) get/put) and `ThreadSafeLRUCache` |
| `avaloka/scheduler.py` | `can_attend_all`, `min_rooms_required` (min-heap), `min_rooms_sweep` (sweep line, cross-check), `assign_rooms` (named rooms) |
| `tests/` | Unit tests, edge cases, and randomized tests against brute-force reference models |
| `benchmarks/bench.py` | Measures per-op cost vs. cache size, n log n scaling, and shows that the unlocked cache corrupts under threads |

**Core solution:** `LRUCache`, `can_attend_all`, `min_rooms_required`.

**Optional extras** (beyond what was asked): `assign_rooms` (discussion Q3), `ThreadSafeLRUCache` (Q4), and `min_rooms_sweep`, a second room-counting method used only to cross-check results in the tests.

## Approach in brief

**LRU cache.** A hash map from key to node gives O(1) lookup, and a doubly linked list keeps the nodes in recency order (most recent after the head, least recent before the tail). Because the map points at list nodes, `get` can move a node to the front by rewiring four pointers, and `put` evicts `tail.prev` when full. Dummy head and tail nodes remove the empty-list and first/last-node special cases. `get` returns `-1` for a missing key.

**Event scheduler.** Events are half-open intervals `[start, end)`, so an event ending at time `t` does not overlap one starting at `t`: `(9, 10)` and `(10, 11)` can share a room.
- `can_attend_all` sorts by start time and checks neighbors: any overlap must show up as `next.start < prev.end`.
- `min_rooms_required` processes events by start time with a min-heap of end times (one per room in use). Before placing an event it frees every room whose end time is `<= start`. The largest the heap gets is the answer.

| Function | Time | Extra space |
|---|---|---|
| `LRUCache.get` / `put` | O(1) average (hash map); the linked-list steps are O(1) worst case | O(1); O(capacity) for the whole cache |
| `can_attend_all` | O(n log n) | O(n) |
| `min_rooms_required` | O(n log n) | O(n) |

## How it's tested

- **LRU:** 200 random sessions × 300 operations compared step by step against an `OrderedDict` reference, checking the full recency order after every operation, plus a structural check that the linked list and the map agree.
- **Scheduler:** 2,000 random event sets checked against a brute-force peak-overlap count; both room algorithms must agree with it. `assign_rooms` is checked to use exactly the minimum number of rooms and never put two overlapping events in the same room.
- **Threads:** 16 threads hammering one cache. The benchmark shows the plain `LRUCache` corrupted in 10/10 runs and `ThreadSafeLRUCache` in 0/10 (it shortens Python's thread switch interval to make races show up reliably).

## Benchmark (Python 3.14, Apple Silicon, median of 3 runs)

| capacity | ns per get/put |
|---:|---:|
| 1,000 | 172 |
| 10,000 | 178 |
| 100,000 | 220 |
| 1,000,000 | 320 |

1000× more entries costs about 1.9× per operation. The algorithm does the same constant work at every size; the rise is consistent with CPU cache misses once the working set no longer fits in cache. Absolute numbers depend on the machine.
