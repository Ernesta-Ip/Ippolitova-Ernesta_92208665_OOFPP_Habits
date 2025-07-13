from db import add_counter, increment_counter, delete_counter, delete_tracker_entries, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
from datetime import datetime

class Counter:

    # TODO: there is an enum type in Python: https://docs.python.org/3/library/enum.html
    #   which module has to define the very value of the period? Counter module? then, why the db module contains any notion
    #   of periods with values? The DB module? then, the Counter module shouldn't redefine them via "TYPE_NAMES".
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

def add_event(name, db, date: datetime = None):
    # .strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    # date.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    increment_counter(db, name, date)

def delete_event(db, name: str):
    """
    Delete a habit and all its records.
    """
    # 1) delete all tracker rows
    delete_tracker_entries(db, name)
    # 2) delete the counter row
    delete_counter(db, name)
