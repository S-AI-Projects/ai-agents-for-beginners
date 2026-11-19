class Memory:
    def __init__(self, capacity=3):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self._capacity = capacity
        self._records = []

    def add(self, record):
        self._records.append(record)
        if len(self._records) > self._capacity:
            self._records.pop(0)

    def records(self):
        return list(self._records)


def fill(records, capacity=3):
    memory = Memory(capacity)
    for record in records:
        memory.add(record)
    return memory.records()


if __name__ == "__main__":
    for label, records, capacity in [
        ("empty", "", 3),
        ("one record", "A", 3),
        ("exactly full", "ABC", 3),
        ("one over", "ABCD", 3),
        ("smallest capacity", "AB", 1),
    ]:
        print(f"{label}: {fill(records, capacity)}")
    for bad in (0, -1, "3", True):
        try:
            Memory(bad)
        except ValueError as error:
            print(f"capacity {bad!r}: {error}")
