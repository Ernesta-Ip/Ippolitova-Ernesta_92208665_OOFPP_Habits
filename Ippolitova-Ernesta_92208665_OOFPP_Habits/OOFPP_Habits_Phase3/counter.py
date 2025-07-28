from db import add_counter, increment_counter, delete_counter, UnitNames, find_counter_by_name
from datetime import datetime

class Counter:

    def __init__(self, name: str, description: str, period_type: UnitNames, period_count: int):
        """
        Counter class for counting habits.
            :param name: name of the habit
            :param description: description of the habit
            :param period_type: type of periodicity (daily, weekly, monthly)
            :param period_count: number of times per chosen period
        """
        self.name = name
        self.description = description
        self.period_type = UnitNames(period_type)
        self.period_count = period_count
        self.count = 0

    def __str__(self):
        """Return a human-readable summary of the counter.
        The string is formatted as:
            "{name}: {count} — {period_count}× per {period_type_label}"

        :return: str: A formatted string combining the counter’s name, total count,
                 rate per period, and the period label (e.g. “daily,” “weekly,” “monthly”).
        """
        return f"{self.name}: {self.count} — {self.period_count}× per {self.period_type.label}"

def add_event(habit_name: str, db, date: datetime = None):
    """
    Add event to habit (check-off the task) by given name, raises increment_counter function.
    :param habit_name: name of the habit in the database
    :param db: a database connection
    :param date: a date of checking-off in datetime format
    :return: None: increments the counter of events
    """
    row = find_counter_by_name(db, habit_name)
    if row is None:
        raise ValueError(f"No such habit: {habit_name!r}")
    counter_id = row
    increment_counter(db, counter_id, date)

def delete_event(db, name: str):
    """
    Delete a habit and all its records.
    """
    _id = find_counter_by_name(db, name)
    delete_counter(db, _id)
