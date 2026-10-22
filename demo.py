"""Walk through both problems with the examples from the assignment."""

from avaloka import LRUCache, assign_rooms, can_attend_all, min_rooms_required

print("== Problem 1: LRU cache (capacity 2) ==")
cache = LRUCache(2)
cache.put(1, "one")
cache.put(2, "two")
print("get(1) ->", cache.get(1), "   ", cache)
cache.put(3, "three")
print("put(3)  -> evicts 2  ", cache)
print("get(2) ->", cache.get(2))

print("\n== Problem 2: event scheduler ==")
for events in ([(9, 10), (10, 11), (11, 12)], [(0, 30), (5, 10), (15, 20)]):
    print(f"events             {events}")
    print(f"can_attend_all     {can_attend_all(events)}")
    print(f"min_rooms_required {min_rooms_required(events)}")
    print(f"assign_rooms       {assign_rooms(events)}\n")
