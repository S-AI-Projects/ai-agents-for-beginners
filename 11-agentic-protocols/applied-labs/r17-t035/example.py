LIMIT = 3


def check_limit(limit):
    if limit < 1:
        raise ValueError("limit must be at least 1")


class BaselineMemory:
    def __init__(self, limit=LIMIT):
        check_limit(limit)
        self._limit = limit
        self._records = []

    def add(self, record):
        self._records.append(record)
        if len(self._records) > self._limit:
            self._records.pop(0)

    def records(self):
        return list(self._records)


def keep_latest(records, limit):
    return records[-limit:]


class Memory:
    def __init__(self, limit=LIMIT):
        check_limit(limit)
        self._limit = limit
        self._records = []

    def add(self, record):
        self._records = keep_latest(self._records + [record], self._limit)

    def records(self):
        return list(self._records)


if __name__ == "__main__":
    for cls in (BaselineMemory, Memory):
        memory = cls()
        for record in "ABCD":
            memory.add(record)
        print(cls.__name__, memory.records())
