from datetime import datetime, timedelta
import db as database

def get_period_type_for(db, name: str) -> database.UnitNames:
    """
    Look up the period_type (1,2,3) for a given habit name.
    Raises ValueError if the habit doesn't exist.

    :return: UnitNames: the enum indicating the period granularity (daily, weekly, monthly)
    """
    _id = database.find_counter_by_name(db, name)
    row = database.get_period_type(db, _id)
    if not row:
        raise ValueError(f"No habit named '{name}'")
    return database.UnitNames(row)

def count_events(db, name: str):
    """
    Counts the number of events for a given habit name
    :return: length: int: the number of events for a given habit name
    """
    _id = database.find_counter_by_name(db, name)
    data = database.get_counter_data(db, _id)
    return len(data)

def group_by_period_type(db):
    """
    Group the data by period type.
    """
    return database.group_by_period_type(db)

def current_streak(period_counts: dict, period_type: database.UnitNames, required: int) -> int:
    """
    Starting from the current period, count how many
    previous periods have count of events >= required (set by user for the exact habit).
    :param period_counts: dict: a dictionary of period index to count
    :param period_type: UnitNames: the enum indicating the period granularity (daily, weekly, monthly)
    :param required: int: the number of times per period the habit is required
    :return: int: streak - the number of consecutive periods in which count >= required.
    """
    streak = 0
    now_idx = period_index(datetime.now(), period_type)
    idx = now_idx
    while period_counts.get(idx, 0) >= required:
        streak += 1
        idx = previous_period(idx, period_type)
    return streak

def longest_streak(period_counts: dict, period_type: database.UnitNames, required: int) -> int:
    """
    Count the maximum number of consecutive periods
    in which count >= required anywhere in the history.
    :param period_counts: dict: a dictionary of period index to count
    :param period_type: UnitNames: the enum indicating the period granularity (daily, weekly, monthly)
    :param required: int: the number of times per period the habit is required
    :return: int: longest - the longest streak found in the history.
    """
    # get all the period‐indices where we met the requirement
    good_periods = sorted(idx for idx, cnt in period_counts.items() if cnt >= required)

    longest = 0
    current = 0
    prev_idx = None

    for idx in good_periods:
        # if this period is exactly the next after prev_idx, extend the run
        if prev_idx is not None and prev_idx == previous_period(idx, period_type):  #
            current += 1
        else:
            # otherwise, start a new run here
            current = 1
        longest = max(longest, current)
        prev_idx = idx
    return longest

def streak_analyse(db, name: str):
    """
    Calculate the longest streak of meeting a counter’s periodic requirement.

    Fetches the period granularity and required count for the given habit,
    then aggregates the counter’s timestamps into period-indexed counts. After that func
    computes the longest consecutive sequence of periods during which the count
    met or exceeded the required threshold.

    :return: tuple: length (number of consecutive periods), period_type (daily, weekly, monthly)
    """
    period_type = get_period_type_for(db, name)
    required = get_period_count_for(db, name)

    # build count-by-period for this habit
    period_counts = {}
    _id = database.find_counter_by_name(db, name)
    for _, ts_str in database.get_counter_data(db, _id):
        ts = datetime.fromisoformat(ts_str)
        idx = period_index(ts, period_type)
        period_counts[idx] = period_counts.get(idx, 0) + 1

    length = longest_streak(period_counts, period_type, required)
    return length, period_type

def period_index(ts: datetime, period_type: database.UnitNames) -> tuple:
    """
    Maps a timestamp to a (year, period) tuple:
    - daily → (YYYY, MM, DD)
    - weekly → (YYYY, ISO_week_number)
    - monthly → (YYYY, MM)
    """
    if period_type is database.UnitNames.PERIOD_DAILY:
        return ts.year, ts.month, ts.day
    elif period_type is database.UnitNames.PERIOD_WEEKLY:
        # iso calendar()[1] gives ISO week number
        return ts.isocalendar()[0], ts.isocalendar()[1]
    elif period_type is database.UnitNames.PERIOD_MONTHLY:
        return ts.year, ts.month
    else:
        raise ValueError("Unknown period type")

def previous_period(idx: tuple, period_type: database.UnitNames) -> tuple:
    """
    Given a period index, return the prior period’s index.
    :param idx: tuple: a period index (year, period unit)
    :param period_type: UnitNames: the enum indicating the period granularity (daily, weekly, monthly)
    ":return: tuple: the prior period index (year, period unit)
    """
    if period_type is database.UnitNames.PERIOD_DAILY:
        dt = datetime(idx[0], idx[1], idx[2]) - timedelta(days=1)
        return dt.year, dt.month, dt.day
    elif period_type is database.UnitNames.PERIOD_WEEKLY:
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
        return dt.isocalendar()[0], dt.isocalendar()[1]
    elif period_type is database.UnitNames.PERIOD_MONTHLY:
        year, month = idx
        if month == 1:
            return year - 1, 12
        else:
            return year, month - 1
    else:
        raise ValueError("Unknown period type")

def next_period(idx: tuple, period_type: database.UnitNames) -> tuple:
    """
    Given a period index, return the next period’s index.
    :param idx: tuple: a period index (year, period unit)
    :param period_type: UnitNames: the enum indicating the period granularity (daily, weekly, monthly)
    :return: tuple: the next period index (year, period unit)
    """
    if period_type is database.UnitNames.PERIOD_DAILY:
        year, month, day = idx
        dt = datetime(year, month, day) + timedelta(days=1)
        return dt.year, dt.month, dt.day

    elif period_type is database.UnitNames.PERIOD_WEEKLY:
        year, week = idx
        # find the Monday of this ISO week
        dt = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")
        dt_next = dt + timedelta(weeks=1)
        return dt_next.isocalendar()[0], dt_next.isocalendar()[1]

    elif period_type is database.UnitNames.PERIOD_MONTHLY:
        year, month = idx
        if month == 12:
            return year + 1, 1
        else:
            return year, month + 1

    else:
        raise ValueError("Unknown period type")

def get_period_count_for(db, name: str) -> int:
    """
    Fetches from the DB how many times per period the habit with a given name is required.
    Raises ValueError if the habit isn't found.
    :return: int: the number of times per period the habit is required.
    """
    _id = database.find_counter_by_name(db, name)
    row = database.get_period_count(db, _id)
    if row is None:
        raise ValueError(f"Habit '{name}' not found in your database.")
    return row
