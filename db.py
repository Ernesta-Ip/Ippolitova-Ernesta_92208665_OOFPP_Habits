import sqlite3
from datetime import datetime

PERIOD_DAILY = 1
PERIOD_WEEKLY = 2
PERIOD_MONTHLY = 3

def get_habit_names(db):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM counter")
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def exist(db, name):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM counter WHERE name = ?", (name,))
    if cursor.fetchone():
        return True
    return False

def get_db(name="main.db"):
    db = sqlite3.connect(name)
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
def add_counter(db, name, description, period_type, period_count):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO counter (name, description, period_type, period_count) VALUES (?, ?, ?, ?)",
        (name, description, period_type, period_count)
    )
    db.commit()

#Addition of event of the exact habit
def increment_counter(db, counter_id, event_time: str = None):
    cur = db.cursor()
    if not event_time:
        event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO tracker (counter_id, timestamp) VALUES (?, ?)",
        (counter_id, event_time)
    )
    db.commit()

#Fetching data on the events of the habit
def get_counter_data(db, counter_id):
    cur = db.cursor()
    cur.execute("SELECT counter_id, timestamp FROM tracker WHERE counter_id = ?", (counter_id,))
    return cur.fetchall()

#Deletion of habit
def delete_counter(db, habit_name: str):
    """
    Remove the habit itself from `counter`.
    """
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM counter WHERE name = ?",
        (habit_name,)
    )
    db.commit()

def delete_tracker_entries(db, habit_name: str):
    """
    Remove all rows from `tracker` for this habit.
    """
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM tracker WHERE counterName = ?",
        (habit_name,)
    )
    db.commit()

