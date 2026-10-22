"""Empirical checks for the complexity claims.

1. LRU get/put cost per operation should stay flat as the cache grows (O(1)).
2. min_rooms_required should grow like n log n.
3. Without a lock, concurrent use of LRUCache can corrupt it; with one, it can't.

Run from the repo root:  python3 -m benchmarks.bench
"""

import random
import sys
import threading
import time

from avaloka import LRUCache, ThreadSafeLRUCache, min_rooms_required

OPS = 200_000


def bench_lru():
    print(f"LRU cache, {OPS:,} mixed get/put ops on a full cache")
    print(f"{'capacity':>12} {'ns per op':>12}")
    for capacity in (1_000, 10_000, 100_000, 1_000_000):
        cache = LRUCache(capacity)
        for k in range(capacity):
            cache.put(k, k)
        rng = random.Random(0)
        keys = [rng.randrange(capacity * 2) for _ in range(OPS)]  # ~50% misses -> evictions
        t0 = time.perf_counter()
        for i, k in enumerate(keys):
            if i & 1:
                cache.get(k)
            else:
                cache.put(k, i)
        ns = (time.perf_counter() - t0) / OPS * 1e9
        print(f"{capacity:>12,} {ns:>12.0f}")


def bench_rooms():
    print("\nmin_rooms_required on random events")
    print(f"{'n events':>12} {'ms':>10} {'ms / (n log2 n) x1e6':>22}")
    import math

    for n in (10_000, 100_000, 1_000_000):
        rng = random.Random(1)
        events = []
        for _ in range(n):
            s = rng.randrange(1_000_000)
            events.append((s, s + rng.randint(1, 5_000)))
        t0 = time.perf_counter()
        min_rooms_required(events)
        ms = (time.perf_counter() - t0) * 1e3
        print(f"{n:>12,} {ms:>10.1f} {ms / (n * math.log2(n)) * 1e6:>22.2f}")


def hammer(cache, threads=16, ops=20_000):
    errors = []

    def worker(seed):
        rng = random.Random(seed)
        try:
            for _ in range(ops):
                k = rng.randint(0, 200)
                if rng.random() < 0.5:
                    cache.put(k, k)
                else:
                    cache.get(k)
        except Exception as exc:
            errors.append(type(exc).__name__)

    ts = [threading.Thread(target=worker, args=(s,)) for s in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    try:
        cache._check_invariants()
    except Exception as exc:
        errors.append(f"invariant broken: {type(exc).__name__}")
    return errors


def bench_threads():
    print("\nConcurrency: 16 threads x 20,000 ops, then structural check")
    sys.setswitchinterval(1e-6)  # force frequent thread switches to expose races
    for cls in (LRUCache, ThreadSafeLRUCache):
        broken = 0
        trials = 10
        for _ in range(trials):
            if hammer(cls(64)):
                broken += 1
        print(f"  {cls.__name__:<20} corrupted in {broken}/{trials} runs")


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}\n")
    bench_lru()
    bench_rooms()
    bench_threads()
