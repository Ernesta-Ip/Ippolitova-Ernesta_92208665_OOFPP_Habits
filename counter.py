from db import add_counter, increment_counter, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY

class Counter:

    TYPE_NAMES = {
        PERIOD_DAILY: "daily",
        PERIOD_WEEKLY: "weekly",
        PERIOD_MONTHLY: "monthly"
    }

    def __init__(self, name: str, description: str, period_type: int, period_count: int):
        self.name = name
        self.description = description
        self.period_type = period_type
        self.period_count = period_count
        self.count = 0

    # def increment(self):
    #     self.count += 1

    # def reset(self):
    #     self.count = 0

    def __str__(self):
        pname = Counter.TYPE_NAMES.get(self.period_type, "?")
        return f"{self.name}: {self.count} — {self.period_count}× per {pname}"

    def store(self, db):
        add_counter(db, self.name, self.description, self.period_type, self.period_count)

def add_event(name, db, date: str = None):
    increment_counter(db, name, date)
