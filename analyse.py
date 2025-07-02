from collections import Counter as _Counter
from datetime import datetime, timedelta
from db import get_counter_data, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY

UNIT_NAMES = {
    PERIOD_DAILY: "daily",
    PERIOD_WEEKLY: "weekly",
    PERIOD_MONTHLY: "monthly"
}

def analyse_counters(db, mode, counter_name=None, streak_type="current"):
    """ Different analytical modes:
      - "count": return int count of events for counter_name (count entries for exact habit)
      - "list_all": return [name, ...] (list of all habits)
      - "group_by_period_type": return { period_type: [name, ...], ... } (list of habits with the same periodicity)
      - "streak": return int streak length (current or longest)
    """
    cur = db.cursor()

    if mode == "count":
        if not counter_name:
            raise ValueError("must pass counter_name for 'count' mode")
        data = get_counter_data(db, counter_name)
        return len(data)

    if mode == "list_all":
        cur.execute("SELECT name FROM counter")
        return [row[0] for row in cur.fetchall()]

    if mode == "group_by_period_type":
        cur.execute("SELECT period_type, name FROM counter")
        rows = cur.fetchall()
        groups = {}
        for period_type, name in rows:
            groups.setdefault(period_type, []).append(name)
        return { UNIT_NAMES.get(k, "?"): v for k,v in groups.items() }

    if mode == "streak":
        if not counter_name:
            raise ValueError("must pass counter_name for 'streak' mode")
        # 1. load metadata for this counter
        cur = db.cursor()
        cur.execute("SELECT period_type, period_count FROM counter WHERE name = ?", (counter_name,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"No habit named '{counter_name}'")
        period_type, period_count = row

        # 2. load and parse timestamps
        raw = get_counter_data(db, counter_name)
        timestamps = [datetime.fromisoformat(ts) for _, ts in raw]

        # 3. bucket and count
        buckets = get_period_counts(timestamps, period_type)

        # 4. choose streak
        if streak_type == "current":
            return current_streak(buckets, period_type, period_count)
        elif streak_type == "longest":
            return longest_streak(buckets, period_type, period_count)
        else:
            raise ValueError("streak_type must be 'current' or 'longest'")


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

def get_period_counts(timestamps: list, period_type: int) -> dict:
    """
    timestamps: list of datetime objects
    returns: { period_index: count_of_events_in_that_period }
    """
    idxs = [period_index(ts, period_type) for ts in timestamps]
    return dict(_Counter(idxs))

def current_streak(period_counts: dict, period_type: int, required: int) -> int:
    """
    Starting from the current period, count how many
    previous periods have count >= required.
    """
    streak = 0
    now_idx = period_index(datetime.now(), period_type)
    idx = now_idx

    while True:
        if period_counts.get(idx, 0) >= required:
            streak += 1
            idx = previous_period(idx, period_type)
        else:
            break

    return streak

def longest_streak(period_counts: dict, period_type: int, required: int) -> int:
    """
    Scan through all occupied periods plus gaps to find the max run.
    """
    if not period_counts:
        return 0

    # get all period indices, sort them, then walk
    all_periods = sorted(period_counts.keys())
    # but also fill in gaps up to “now” so runs stop at missing periods
    # build a complete list from earliest to now, stepping period by period
    start = all_periods[0]
    end = period_index(datetime.now(), period_type)

    seq = []
    idx = start
    while True:
        seq.append(idx)
        if idx == end:
            break
        idx = previous_period(idx, period_type)
    # seq is descending; reverse to ascending
    seq.reverse()

    max_run = run = 0
    for idx in seq:
        if period_counts.get(idx, 0) >= required:
            run += 1
            if run > max_run:
                max_run = run
        else:
            run = 0

    return max_run
