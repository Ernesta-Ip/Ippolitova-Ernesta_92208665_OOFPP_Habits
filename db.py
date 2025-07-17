import sqlite3
from datetime import datetime
from enum import IntEnum
from xmlrpc.client import DateTime

class UnitNames(IntEnum):
    PERIOD_DAILY   = 1
    PERIOD_WEEKLY  = 2
    PERIOD_MONTHLY = 3

    @property
    def label(self) -> str:
        return self.name.split('_', 1)[1].lower()

PERIOD_DAILY = UnitNames.PERIOD_DAILY
PERIOD_WEEKLY = UnitNames.PERIOD_WEEKLY
PERIOD_MONTHLY = UnitNames.PERIOD_MONTHLY

def get_habit_names(db):
    """
    Fetches the names of all the habits in the database.
    """
    cursor = db.cursor()
    cursor.execute("SELECT name FROM counter")
    rows = cursor.fetchall()
    if not rows:
        return []
    return [row[0] for row in rows]

def exist(db, _id):
    """
    Checks if the habit exists in the database.
    """
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM counter WHERE id = ?", (_id,))
    if cursor.fetchone():
        return True
    return False

def get_db(name="main.db"):
    import os
    print(os.path.abspath(name))
    db = sqlite3.connect(name)
    db.execute("PRAGMA foreign_keys = ON;")
    create_tables(db)
    return db

def create_tables(db):
    """
    Initial creation of tables counter and tracker.
    Makes commit to the database after the creation.
    """
    cur = db.cursor()

    # ——— Table counter ———
    cur.execute("""
    CREATE TABLE IF NOT EXISTS counter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        period_type INTEGER NOT NULL CHECK(period_type IN (1,2,3)),
        period_count INTEGER NOT NULL
    )
    """)

    # ——— Table tracker ———
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        counter_id INTEGER NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY(counter_id) REFERENCES counter(id) ON DELETE CASCADE
    )
    """)

    db.commit()


def add_counter(db, name, description, period_type: UnitNames, period_count):
    """
    Add habit to the database and makes commit to the database
    :param db: database connection
    :param name: name of the habit
    :param description: text description of the habit
    :param period_type: enum value (day, week, month)
    :param period_count: int number of times per period type
    :return: ID of the inserted row
    """
    cur = db.cursor()
    cur.execute(
        "INSERT INTO counter (name, description, period_type, period_count) VALUES (?, ?, ?, ?)",
        (name, description, period_type, period_count)
    )
    db.commit()
    return cur.lastrowid

def group_by_period_type(db):
    """
    Lists habits grouped by period type.
    """
    cur = db.cursor()
    cur.execute("SELECT period_type, GROUP_CONCAT(name) GroupedNames FROM counter GROUP BY period_type")
    return cur.fetchall()

def get_period_count(db, _id):
    """
    Selects the period count for the given habit by ID.
    """
    cur = db.cursor()
    cur.execute("SELECT period_count FROM counter WHERE id = ?", (_id,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

def get_period_type(db, _id):
    """
    Selects the period type for the given habit by ID.
    """
    cur = db.cursor()
    cur.execute("SELECT period_type FROM counter WHERE id = ?", (_id,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

def find_counter_by_name(db, name):
    """
    Fetches the ID of the habit with the given name.
    :return: the value of ID column for the first matching row, or None if no such habit exists.
    """
    cur = db.cursor()
    cur.execute("SELECT id FROM counter WHERE name = ?", (name,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

def increment_counter(db, counter_id, event_time: DateTime = None):
    """
    Inserts the event with the timestamp into the tracker table.
    """
    if not event_time:
        event_time = datetime.now()

    event_time_string = event_time.strftime("%Y-%m-%d %H:%M:%S")

    cur = db.cursor()
    cur.execute(
        "INSERT INTO tracker (counter_id, timestamp) VALUES (?, ?)",
        (counter_id, event_time_string)
    )
    db.commit()

def get_counter_data(db, counter_id : int):
    """
    Fetches the events of the habit with the given ID.
    """
    cur = db.cursor()
    cur.execute("SELECT counter_id, timestamp FROM tracker WHERE counter_id = ?", (counter_id,))
    return cur.fetchall()

def delete_counter(db, _id: int):
    """
    Remove the habit itself from `counter`.
    """
    cursor = db.cursor()
    cursor.execute("DELETE FROM counter WHERE id = ?", (_id,))
    db.commit()
