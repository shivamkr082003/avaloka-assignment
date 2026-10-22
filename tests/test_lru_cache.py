import random
import threading
import unittest
from collections import OrderedDict

from avaloka import LRUCache, ThreadSafeLRUCache


class ReferenceLRU:
    """Obviously-correct (but not O(1)-by-design) model to compare against."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data.move_to_end(key)
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = value


class TestLRUCacheBasics(unittest.TestCase):
    def test_classic_example(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)   # order now: 1, 2
        cache.put(3, 3)                     # evicts 2
        self.assertEqual(cache.get(2), -1)
        cache.put(4, 4)                     # evicts 1
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(4), 4)

    def test_get_missing_returns_minus_one(self):
        self.assertEqual(LRUCache(1).get("nope"), -1)

    def test_get_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")          # "b" is now least recent
        cache.put("c", 3)
        self.assertIn("a", cache)
        self.assertNotIn("b", cache)

    def test_update_existing_key_does_not_evict(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 10)      # update, cache still full but no eviction
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache.get("a"), 10)
        self.assertEqual(cache.get("b"), 2)

    def test_update_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 3)       # "b" is now least recent
        cache.put("c", 4)
        self.assertEqual(cache.keys_mru_to_lru(), ["c", "a"])

    def test_capacity_one(self):
        cache = LRUCache(1)
        cache.put(1, "x")
        cache.put(2, "y")
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), "y")
        cache._check_invariants()

    def test_falsy_values_are_stored(self):
        cache = LRUCache(3)
        cache.put("zero", 0)
        cache.put("none", None)
        cache.put("empty", "")
        self.assertEqual(cache.get("zero"), 0)
        self.assertIsNone(cache.get("none"))
        self.assertEqual(cache.get("empty"), "")

    def test_contains_and_len_do_not_change_order(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        _ = "a" in cache
        _ = len(cache)
        cache.put("c", 3)       # "a" is still least recent, so it goes
        self.assertNotIn("a", cache)

    def test_invalid_capacity(self):
        for bad in (0, -1):
            with self.assertRaises(ValueError):
                LRUCache(bad)
        for bad in (1.5, "2", None, True):
            with self.assertRaises(TypeError):
                LRUCache(bad)


class TestLRUCacheRandomized(unittest.TestCase):
    def test_matches_reference_model(self):
        rng = random.Random(2026)
        for _ in range(200):
            capacity = rng.randint(1, 8)
            ours, ref = LRUCache(capacity), ReferenceLRU(capacity)
            for _ in range(300):
                key = rng.randint(0, 12)
                if rng.random() < 0.5:
                    self.assertEqual(ours.get(key), ref.get(key))
                else:
                    val = rng.randint(0, 1000)
                    ours.put(key, val)
                    ref.put(key, val)
                self.assertEqual(ours.keys_mru_to_lru(), list(reversed(ref.data)))
            ours._check_invariants()


class TestThreadSafeLRUCache(unittest.TestCase):
    def test_concurrent_access_keeps_structure_valid(self):
        cache = ThreadSafeLRUCache(64)
        errors = []

        def worker(seed):
            rng = random.Random(seed)
            try:
                for _ in range(5000):
                    key = rng.randint(0, 200)
                    if rng.random() < 0.5:
                        cache.put(key, key * 2)
                    else:
                        value = cache.get(key)
                        if value != -1 and value != key * 2:
                            errors.append((key, value))
            except Exception as exc:  # surface crashes from worker threads
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(s,)) for s in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        self.assertLessEqual(len(cache), 64)
        cache._check_invariants()


if __name__ == "__main__":
    unittest.main()
