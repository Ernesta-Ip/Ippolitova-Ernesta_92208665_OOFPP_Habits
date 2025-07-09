from collections import Counter as _Counter
from datetime import datetime, timedelta
from db import get_counter_data, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY

UNIT_NAMES = {
    PERIOD_DAILY: "daily",
    PERIOD_WEEKLY: "weekly",
    PERIOD_MONTHLY: "monthly"
}

def get_period_type_for(name: str, db) -> int:
    """
    Look up the period_type (1,2,3) for a given habit name.
    Raises ValueError if the habit doesn't exist.
    """
    cur = db.cursor()
    cur.execute("SELECT period_type FROM counter WHERE name = ?", (name,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"No habit named '{name}'")
    return row[0]

def count_events(db, counter_name=None):
    if not counter_name:
        raise ValueError("must pass counter_name for 'count' mode")
    data = get_counter_data(db, counter_name)
    return len(data)

def list_all(db):
    cur = db.cursor()
    cur.execute("SELECT name FROM counter")
    return [row[0] for row in cur.fetchall()]

def group_by_period_type (db):
    cur = db.cursor()
    cur.execute("SELECT period_type, name FROM counter")
    rows = cur.fetchall()
    groups = {}
    for period_type, name in rows:
        groups.setdefault(period_type, []).append(name)
    return { UNIT_NAMES.get(k, "?"): v for k,v in groups.items() }

def current_streak(period_counts: dict, period_type: int, required: int) -> int:
    """
    Starting from the current period, count how many
    previous periods have count >= required.
    """
    streak = 0
    now_idx = period_index(datetime.now(), period_type)
    idx = now_idx

    while period_counts.get(idx, 0) >= required:
        streak += 1
        idx = previous_period(idx, period_type)
    return streak

def longest_streak(period_counts: dict, period_type: int, required: int) -> int:
    """
    Count the maximum number of consecutive periods
    in which count >= required anywhere in the history.
    """
    # get all the period‐indices where we met the requirement
    good_periods = sorted(idx for idx, cnt in period_counts.items() if cnt >= required)

    longest = 0
    current = 0
    prev_idx = None

    for idx in good_periods:
        # if this period is exactly the next after prev_idx, extend the run
        if prev_idx is not None and idx == next_period(prev_idx, period_type):
            current += 1
        else:
            # otherwise start a new run here
            current = 1
        longest = max(longest, current)
        prev_idx = idx

    return longest


def period_index(ts: datetime, period_type: int) -> tuple:
    """
    Maps a timestamp to a (year, period) tuple:
    - daily → (YYYY, MM, DD)
    - weekly → (YYYY, ISO_week_number)
    - monthly → (YYYY, MM)
    """
    if period_type == PERIOD_DAILY:
        return (ts.year, ts.month, ts.day)
    elif period_type == PERIOD_WEEKLY:
        # iso calendar()[1] gives ISO week number
        return (ts.isocalendar()[0], ts.isocalendar()[1])
    elif period_type == PERIOD_MONTHLY:
        return (ts.year, ts.month)
    else:
        raise ValueError("Unknown period type")

def previous_period(idx: tuple, period_type: int) -> tuple:
    """
    Given a period index, return the prior period’s index.
    """
    if period_type == PERIOD_DAILY:
        dt = datetime(idx[0], idx[1], idx[2]) - timedelta(days=1)
        return (dt.year, dt.month, dt.day)
    elif period_type == PERIOD_WEEKLY:
        # Convert back to a date, subtract 1 week
        # Use Monday of that ISO week:
        year, week = idx
        if week == 1:
            # go to the last week of the previous year
            year -= 1
            week = datetime(year, 12, 28).isocalendar()[1]
        else:
            week -= 1
        dt = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")
        return (dt.isocalendar()[0], dt.isocalendar()[1])
    elif period_type == PERIOD_MONTHLY:
        year, month = idx
        if month == 1:
            return (year - 1, 12)
        else:
            return (year, month - 1)
    else:
        raise ValueError("Unknown period type")

def next_period(idx: tuple, period_type: int) -> tuple:
    """
    Given a period index, return the next period’s index.
    """
    if period_type == PERIOD_DAILY:
        year, month, day = idx
        dt = datetime(year, month, day) + timedelta(days=1)
        return (dt.year, dt.month, dt.day)

    elif period_type == PERIOD_WEEKLY:
        year, week = idx
        # find the Monday of this ISO week
        dt = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")
        dt_next = dt + timedelta(weeks=1)
        return (dt_next.isocalendar()[0], dt_next.isocalendar()[1])

    elif period_type == PERIOD_MONTHLY:
        year, month = idx
        if month == 12:
            return (year + 1, 1)
        else:
            return (year, month + 1)

    else:
        raise ValueError("Unknown period type")


def get_period_counts(timestamps: list, period_type: int) -> dict:
    """
    timestamps: list of datetime objects
    returns: { period_index: count_of_events_in_that_period }
    """
    idxs = [period_index(ts, period_type) for ts in timestamps]
    return dict(_Counter(idxs))

def get_period_count_for(name: str, db) -> int:
    """
    Fetches from the DB how many times per period the habit 'name' is required.
    Raises ValueError if the habit isn't found.
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT period_count FROM counter WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Habit '{name}' not found in your database.")
    return row[0]

