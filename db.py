import sqlite3
from datetime import datetime

PERIOD_DAILY = 1
PERIOD_WEEKLY = 2
PERIOD_MONTHLY = 3

def get_db(name="main.db"):
    db = sqlite3.connect(name)
    create_tables(db)
    return db

def create_tables(db):
    cur = db.cursor()

    # ——— Table counter ———
    cur.execute("""
    CREATE TABLE IF NOT EXISTS counter (
        name TEXT PRIMARY KEY,
        description TEXT,
        period_type INTEGER NOT NULL CHECK(period_type IN (1,2,3)),
        period_count INTEGER NOT NULL
    )
    """)

    try:
        cur.execute("ALTER TABLE counter ADD COLUMN period_type INTEGER NOT NULL DEFAULT 1")
        cur.execute("ALTER TABLE counter ADD CHECK(period_type IN (1,2,3))")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE counter ADD COLUMN period_count INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # ——— Table tracker ———
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tracker (
        counterName TEXT,
        timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY(counterName) REFERENCES counter(name)
    )
    """)

    #migration for the previous tracker table without timestamp
    cur.execute("PRAGMA table_info(tracker)")
    cols = [row[1] for row in cur.fetchall()]
    if 'timestamp' not in cols:
        cur.execute("ALTER TABLE tracker RENAME TO tracker_old")
        cur.execute("""
        CREATE TABLE tracker (
            counterName TEXT,
            timestamp DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(counterName) REFERENCES counter(name)
        )
        """)
        # copy old tables
        cur.execute("""
        INSERT INTO tracker (counterName, timestamp)
        SELECT counterName, CURRENT_TIMESTAMP
        FROM tracker_old
        """)
        #delete old table
        cur.execute("DROP TABLE tracker_old")

    db.commit()

def add_counter(db, name, description, period_type, period_count):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO counter (name, description, period_type, period_count) VALUES (?, ?, ?, ?)",
        (name, description, period_type, period_count)
    )
    db.commit()

def increment_counter(db, name, event_time: str = None):
    cur = db.cursor()
    if not event_time:
        event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO tracker (counterName, timestamp) VALUES (?, ?)",
        (name, event_time)
    )
    db.commit()

def get_counter_data(db, name):
    cur = db.cursor()
    cur.execute("SELECT counterName, timestamp FROM tracker WHERE counterName = ?", (name,))
    return cur.fetchall()
