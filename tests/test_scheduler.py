import random
import unittest

from avaloka import (
    assign_rooms,
    can_attend_all,
    min_rooms_required,
    min_rooms_sweep,
    room_name,
)


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def brute_force_rooms(events):
    """Peak concurrency: the busiest moment is always some event's start."""
    return max((sum(1 for s, e in events if s <= t < e) for t, _ in events), default=0)


def random_events(rng, n, horizon=24):
    events = []
    for _ in range(n):
        start = rng.randint(0, horizon - 1)
        events.append((start, rng.randint(start + 1, horizon)))
    return events


class TestCanAttendAll(unittest.TestCase):
    def test_spec_example_back_to_back(self):
        self.assertTrue(can_attend_all([(9, 10), (10, 11), (11, 12)]))

    def test_overlap(self):
        self.assertFalse(can_attend_all([(9, 11), (10, 12)]))

    def test_unsorted_input(self):
        self.assertTrue(can_attend_all([(11, 12), (9, 10), (10, 11)]))
        self.assertFalse(can_attend_all([(13, 15), (9, 10), (14, 16)]))

    def test_containment_is_overlap(self):
        self.assertFalse(can_attend_all([(9, 17), (12, 13)]))

    def test_identical_events_overlap(self):
        self.assertFalse(can_attend_all([(9, 10), (9, 10)]))

    def test_empty_and_single(self):
        self.assertTrue(can_attend_all([]))
        self.assertTrue(can_attend_all([(1, 2)]))

    def test_float_times(self):
        self.assertTrue(can_attend_all([(9.0, 9.5), (9.5, 10.25)]))
        self.assertFalse(can_attend_all([(9.0, 9.6), (9.5, 10.25)]))

    def test_does_not_mutate_input(self):
        events = [(3, 4), (1, 2)]
        can_attend_all(events)
        self.assertEqual(events, [(3, 4), (1, 2)])


class TestMinRooms(unittest.TestCase):
    CASES = [
        ([], 0),
        ([(9, 10)], 1),
        ([(9, 10), (10, 11), (11, 12)], 1),       # spec example
        ([(0, 30), (5, 10), (15, 20)], 2),
        ([(1, 5), (2, 6), (3, 7), (4, 8)], 4),
        ([(1, 5), (5, 10), (1, 5), (5, 10)], 2),  # adjacency reuses rooms
        ([(1, 10), (2, 3), (3, 4), (4, 5)], 2),
        ([(9, 10), (9, 10), (9, 10)], 3),
    ]

    def test_known_cases_both_algorithms(self):
        for events, expected in self.CASES:
            with self.subTest(events=events):
                self.assertEqual(min_rooms_required(events), expected)
                self.assertEqual(min_rooms_sweep(events), expected)

    def test_randomized_against_brute_force(self):
        rng = random.Random(7)
        for _ in range(2000):
            events = random_events(rng, rng.randint(0, 25))
            expected = brute_force_rooms(events)
            self.assertEqual(min_rooms_required(events), expected, events)
            self.assertEqual(min_rooms_sweep(events), expected, events)

    def test_consistent_with_can_attend_all(self):
        rng = random.Random(11)
        for _ in range(1000):
            events = random_events(rng, rng.randint(0, 8))
            self.assertEqual(can_attend_all(events), min_rooms_required(events) <= 1)


class TestValidation(unittest.TestCase):
    def test_rejects_bad_events(self):
        for bad in ([(5, 5)], [(6, 5)], [(1,)], [(1, 2, 3)], [None]):
            for fn in (can_attend_all, min_rooms_required, min_rooms_sweep, assign_rooms):
                with self.subTest(fn=fn.__name__, events=bad), self.assertRaises(ValueError):
                    fn(bad)


class TestAssignRooms(unittest.TestCase):
    def test_spec_example_single_room(self):
        self.assertEqual(
            assign_rooms([(9, 10), (10, 11), (11, 12)]),
            ["Room A", "Room A", "Room A"],
        )

    def test_output_aligned_with_input_order(self):
        events = [(15, 20), (0, 30), (5, 10)]
        self.assertEqual(assign_rooms(events), ["Room B", "Room A", "Room B"])

    def test_randomized_assignment_is_valid_and_optimal(self):
        rng = random.Random(3)
        for _ in range(1000):
            events = random_events(rng, rng.randint(0, 25))
            rooms = assign_rooms(events)
            self.assertEqual(len(rooms), len(events))
            self.assertEqual(len(set(rooms)), min_rooms_required(events))
            for i in range(len(events)):
                for j in range(i + 1, len(events)):
                    if rooms[i] == rooms[j]:
                        self.assertFalse(overlaps(events[i], events[j]))

    def test_room_names(self):
        self.assertEqual(room_name(0), "Room A")
        self.assertEqual(room_name(25), "Room Z")
        self.assertEqual(room_name(26), "Room AA")
        self.assertEqual(room_name(27), "Room AB")
        self.assertEqual(room_name(701), "Room ZZ")
        self.assertEqual(room_name(702), "Room AAA")


if __name__ == "__main__":
    unittest.main()
