import unittest

from example import Memory, fill


class BoundaryTests(unittest.TestCase):
    def test_empty_memory(self):
        self.assertEqual(fill(""), [])

    def test_single_record(self):
        self.assertEqual(fill("A"), ["A"])

    def test_exactly_at_capacity_evicts_nothing(self):
        self.assertEqual(fill("ABC"), ["A", "B", "C"])

    def test_one_past_capacity_evicts_the_oldest(self):
        self.assertEqual(fill("ABCD"), ["B", "C", "D"])

    def test_smallest_valid_capacity_keeps_only_the_newest(self):
        self.assertEqual(fill("AB", capacity=1), ["B"])

    def test_invalid_capacities_are_rejected(self):
        for bad in (0, -1, "3", 2.5, True, None):
            with self.subTest(bad):
                with self.assertRaises(ValueError):
                    Memory(bad)

    def test_returned_list_is_a_copy(self):
        memory = Memory()
        for record in "ABCD":
            memory.add(record)
        memory.records().append("X")
        self.assertEqual(memory.records(), ["B", "C", "D"])


if __name__ == "__main__":
    unittest.main()
