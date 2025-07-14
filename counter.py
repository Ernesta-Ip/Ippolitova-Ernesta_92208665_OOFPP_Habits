from db import add_counter, increment_counter, delete_counter, delete_tracker_entries, UnitNames
from datetime import datetime

class Counter:

    def __init__(self, name: str, description: str, period_type: UnitNames, period_count: int):
        self.name = name
        self.description = description
        self.period_type = UnitNames(period_type)
        self.period_count = period_count
        self.count = 0

    def __str__(self):
        return f"{self.name}: {self.count} — {self.period_count}× per {self.period_type.label}"

    def store(self, db):
        add_counter(db, self.name, self.description, self.period_type, self.period_count)

def add_event(habit_name: str, db, date: datetime = None):
    cur = db.cursor()
    cur.execute("SELECT id FROM counter WHERE name = ?", (habit_name,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"No such habit: {habit_name!r}")
    counter_id = row[0]
    increment_counter(db, counter_id, date)

def delete_event(db, name: str):
    """
    Delete a habit and all its records.
    """
    delete_counter(db, name)
