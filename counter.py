from db import add_counter, increment_counter, delete_counter, delete_tracker_entries, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY

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

    def __str__(self):
        pname = Counter.TYPE_NAMES.get(self.period_type, "?")
        return f"{self.name}: {self.count} — {self.period_count}× per {pname}"

    def store(self, db):
        add_counter(db, self.name, self.description, self.period_type, self.period_count)

def add_event(name, db, date: str = None):
    increment_counter(db, name, date)

def delete_event(db, name: str):
    """
    Delete a habit and all its records.
    """
    # 1) delete all tracker rows
    delete_tracker_entries(db, name)
    # 2) delete the counter row
    delete_counter(db, name)
