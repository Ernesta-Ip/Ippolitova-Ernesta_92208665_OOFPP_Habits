from db import get_counter_data, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY

# reuse the same human-readable names that Counter.__str__ does
TYPE_NAMES = {
    PERIOD_DAILY: "daily",
    PERIOD_WEEKLY: "weekly",
    PERIOD_MONTHLY: "monthly"
}

def analyse_counters(db, mode, counter_name=None):
    """ Different analytical modes:
      - "count": return int count of events for counter_name (count entries for exact habit)
      - "list_all": return [name, ...] (list of all habits)
      - "group_by_period_type": return { period_type: [name, ...], ... } (list of habits with the same periodicity)
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
        return { TYPE_NAMES.get(k, "?"): v for k,v in groups.items() }
