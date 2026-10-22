# Avaloka take-home: LRU Cache & Event Scheduler

Shivam Kumar, for the AI / Multi-Agent Systems Intern role at Avaloka (Guruvai Sciences).

Pure Python 3.10+, standard library only. Nothing to install.

```bash
python3 demo.py                                   # examples from the assignment
python3 -m unittest discover -s tests -t . -v     # 27 tests
python3 -m benchmarks.bench                       # complexity + concurrency evidence
```

## Layout

| File | What it contains |
|---|---|
| `avaloka/lru_cache.py` | `LRUCache` (hash map + doubly linked list with sentinels, O(1) get/put) and `ThreadSafeLRUCache` |
| `avaloka/scheduler.py` | `can_attend_all`, `min_rooms_required` (min-heap), `min_rooms_sweep` (sweep line, cross-check), `assign_rooms` (named rooms) |
| `tests/` | Unit tests, edge cases, and randomized tests against brute-force reference models |
| `benchmarks/bench.py` | Measures per-op cost vs. cache size, n log n scaling, and shows that the unlocked cache corrupts under threads |

## How it's tested

- **LRU:** 200 random sessions × 300 operations compared step by step against an `OrderedDict` reference, checking the full recency order after every operation, plus a structural check that the linked list and the map agree.
- **Scheduler:** 2,000 random event sets checked against a brute-force peak-overlap count; both room algorithms must agree with it. `assign_rooms` is checked to use exactly the minimum number of rooms and never put two overlapping events in the same room.
- **Threads:** 16 threads hammering one cache. The benchmark shows the plain `LRUCache` corrupted in 10/10 runs and `ThreadSafeLRUCache` in 0/10.

## Benchmark (Python 3.14, Apple Silicon, median of 3 runs)

| capacity | ns per get/put |
|---:|---:|
| 1,000 | 172 |
| 10,000 | 178 |
| 100,000 | 220 |
| 1,000,000 | 320 |

1000× more entries costs about 1.9× per operation. The algorithm does the same constant work at every size; the rise is consistent with CPU cache misses once the working set no longer fits in cache.
# avaloka-assignment
# avaloka-assignment
