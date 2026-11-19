import unittest

from example import BaselineMemory, Memory, keep_latest


def fill(cls, records, limit=3):
    memory = cls(limit)
    for record in records:
        memory.add(record)
    return memory


class MemoryTests(unittest.TestCase):
    def test_abcd_retains_bcd(self):
        for cls in (BaselineMemory, Memory):
            with self.subTest(cls.__name__):
                self.assertEqual(fill(cls, "ABCD").records(), ["B", "C", "D"])

    def test_returned_list_is_a_copy(self):
        for cls in (BaselineMemory, Memory):
            with self.subTest(cls.__name__):
                memory = fill(cls, "ABCD")
                memory.records().append("X")
                memory.records().clear()
                self.assertEqual(memory.records(), ["B", "C", "D"])

    def test_refactor_matches_baseline_on_every_prefix(self):
        for size in range(0, 8):
            for limit in (1, 2, 3, 5):
                with self.subTest(size=size, limit=limit):
                    records = list("ABCDEFG")[:size]
                    self.assertEqual(
                        fill(BaselineMemory, records, limit).records(),
                        fill(Memory, records, limit).records(),
                    )

    def test_keep_latest_alone(self):
        self.assertEqual(keep_latest(["A", "B", "C", "D"], 3), ["B", "C", "D"])

    def test_zero_limit_is_rejected(self):
        for cls in (BaselineMemory, Memory):
            with self.subTest(cls.__name__):
                with self.assertRaises(ValueError):
                    cls(0)


if __name__ == "__main__":
    unittest.main()
