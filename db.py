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
    cursor = db.cursor()
    cursor.execute("SELECT name FROM counter")
    rows = cursor.fetchall()
    if not rows:
        return []
    return [row[0] for row in rows]

def exist(db, _id):
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

# Initial creation of tables counter and tracker
def create_tables(db):
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

#Addition of new habit
def add_counter(db, name, description, period_type: UnitNames, period_count):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO counter (name, description, period_type, period_count) VALUES (?, ?, ?, ?)",
        (name, description, period_type, period_count)
    )
    db.commit()
    return cur.lastrowid

def group_by_period_type(db):
    cur = db.cursor()
    cur.execute("SELECT period_type, GROUP_CONCAT(name) GroupedNames FROM counter GROUP BY period_type")
    return cur.fetchall()

def get_period_count(db, _id):
    cur = db.cursor()
    cur.execute("SELECT period_count FROM counter WHERE id = ?", (_id,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

def get_period_type(db, _id):
    cur = db.cursor()
    cur.execute("SELECT period_type FROM counter WHERE id = ?", (_id,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

def find_counter_by_name(db, name):
    cur = db.cursor()
    cur.execute("SELECT id FROM counter WHERE name = ?", (name,))
    rows = cur.fetchone()
    if rows is not None:
        return rows[0]
    return None

#Addition of event of the exact habit
def increment_counter(db, counter_id, event_time: DateTime = None):

    if not event_time:
        event_time = datetime.now()

    event_time_string = event_time.strftime("%Y-%m-%d %H:%M:%S")

    cur = db.cursor()
    cur.execute(
        "INSERT INTO tracker (counter_id, timestamp) VALUES (?, ?)",
        (counter_id, event_time_string)
    )
    db.commit()

#Fetching data on the events of the habit
def get_counter_data(db, counter_id : int):
    cur = db.cursor()
    cur.execute("SELECT counter_id, timestamp FROM tracker WHERE counter_id = ?", (counter_id,))
    return cur.fetchall()

#Deletion of habit
def delete_counter(db, _id: int):
    """
    Remove the habit itself from `counter`.
    """
    cursor = db.cursor()
    cursor.execute("DELETE FROM counter WHERE id = ?", (_id,))
    db.commit()
