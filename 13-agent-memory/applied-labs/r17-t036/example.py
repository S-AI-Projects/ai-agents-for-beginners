class Memory:
    def __init__(self, capacity):
        self._capacity = capacity
        self._records = []

    def add(self, record):
        self._records.append(record)
        if len(self._records) > self._capacity:
            self._records.pop(0)

    def records(self):
        return list(self._records)


STREAM = list("ABCDEF")
WINDOW = 3


def evaluate(capacities=(1, 3, 5), stream=STREAM, window=WINDOW):
    rows = []
    for capacity in capacities:
        memory = Memory(capacity)
        for record in stream:
            memory.add(record)
        kept = memory.records()
        newest = stream[-window:]
        rows.append(
            {
                "capacity": capacity,
                "kept": kept,
                "correct": kept == stream[-capacity:],
                "recall_newest": round(sum(r in kept for r in newest) / len(newest), 2),
            }
        )
    return rows


if __name__ == "__main__":
    print("capacity  kept             correct  recall_newest")
    for row in evaluate():
        print(f"{row['capacity']:<9} {''.join(row['kept']):<16} {str(row['correct']):<8} {row['recall_newest']}")
