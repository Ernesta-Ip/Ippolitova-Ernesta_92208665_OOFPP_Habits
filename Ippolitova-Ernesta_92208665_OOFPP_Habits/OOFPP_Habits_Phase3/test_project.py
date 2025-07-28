# tests/test_project.py
import pytest
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

from db import (
    create_tables, add_counter, get_habit_names, exist,
    find_counter_by_name, get_period_count, get_period_type,
    increment_counter, get_counter_data, group_by_period_type,
    delete_counter, UnitNames
)
from analyse import (
    count_events,
    period_index, previous_period, next_period,
    longest_streak, streak_analyse
)

class TestDB:
    def setup_method(self, method):
        # create a temporary sqlite file
        tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tf.close()
        self.db_path = tf.name

        # open & initialize
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA foreign_keys = ON;")

    def teardown_method(self, method):
        self.db.close()
        os.remove(self.db_path)

    def test_create_tables(self):
        select_string = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor = self.db.cursor()

        cursor.execute(select_string)
        tables = cursor.fetchall()

        assert "counter" not in [item[0] for item in tables]
        assert "tracker" not in [item[0] for item in tables]

        create_tables(self.db)

        cursor.execute(select_string)
        tables = cursor.fetchall()

        assert "counter" in [item[0] for item in tables]
        assert "tracker" in [item[0] for item in tables]

    def test_add_counter(self):
        create_tables(self.db)
        add_counter(self.db, "run", "running daily", UnitNames.PERIOD_DAILY, 1)
        assert exist(self.db, 1)


class TestFunctions:
    def setup_method(self, method):
        # create a temporary sqlite file
        tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tf.close()
        self.db_path = tf.name

        # open & initialize
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA foreign_keys = ON;")
        create_tables(self.db)
        self.dt = datetime(2025, 7, 17, 15, 0, 0)

        # seed habits #
        add_counter(self.db, "run",  "running daily",  UnitNames.PERIOD_DAILY,  1)
        add_counter(self.db, "yoga", "weekly yoga",    UnitNames.PERIOD_WEEKLY, 2)
        add_counter(self.db, "water",  "hydration",  UnitNames.PERIOD_DAILY,  4)
        add_counter(self.db, "gym", "weekly yoga",    UnitNames.PERIOD_WEEKLY, 3)

    def test_add_and_find(self):
        names = get_habit_names(self.db)
        assert set(names) == {"run", "yoga", "water", "gym"}

        run_id = find_counter_by_name(self.db, "run")
        assert isinstance(run_id, int)
        assert run_id == 1
        assert exist(self.db, run_id)

        assert get_period_count(self.db, run_id) == 1
        assert get_period_type(self.db, run_id) == UnitNames.PERIOD_DAILY

    def test_increment_and_fetch(self):
        run_id = find_counter_by_name(self.db, "run")
        assert get_counter_data(self.db, run_id) == []

        increment_counter(self.db, run_id, datetime(2025, 7, 17, 12, 0, 0))
        increment_counter(self.db, run_id, datetime(2025, 7, 17, 13, 0, 0))
        increment_counter(self.db, run_id, datetime(2025, 7, 17, 14, 0, 0))

        rows = get_counter_data(self.db, run_id)
        assert len(rows) == 3

    def test_count_events_helper(self):
        water_id = find_counter_by_name(self.db, "water")
        assert count_events(self.db, "water") == 0
        increment_counter(self.db, water_id, datetime(2025, 6, 17, 12, 0, 0))
        increment_counter(self.db, water_id, datetime(2025, 7, 17, 13, 0, 0))
        increment_counter(self.db, water_id, datetime(2025, 7, 17, 14, 0, 0))
        increment_counter(self.db, water_id, datetime(2025, 7, 17, 15, 0, 0))

        # count_events uses the analyse.count_events wrapper
        assert count_events(self.db, "water") == 4

    def test_group_by_period_type(self):
        groups : dict[int, str]
        groups = dict(group_by_period_type(self.db))

        # PERIOD_DAILY → run; WEEKLY → yoga
        assert UnitNames.PERIOD_DAILY in groups
        assert "run" in groups[UnitNames.PERIOD_DAILY]
        assert "yoga" in groups[UnitNames.PERIOD_WEEKLY]
        assert "water" in groups[UnitNames.PERIOD_DAILY]
        assert "gym" in groups[UnitNames.PERIOD_WEEKLY]

    def test_delete_counter(self):
        yoga_id = find_counter_by_name(self.db, "yoga")
        assert find_counter_by_name(self.db, "yoga") is not None
        delete_counter(self.db, yoga_id)
        assert find_counter_by_name(self.db, "yoga") is None

    def teardown_method(self, method):
        self.db.close()
        os.remove(self.db_path)

    def test_period_index_and_navigation(self):
        # daily
        idx = period_index(self.dt, UnitNames.PERIOD_DAILY)
        assert idx == (2025, 7, 17)
        assert previous_period(idx, UnitNames.PERIOD_DAILY) == (2025, 7, 16)
        assert next_period(previous_period(idx, UnitNames.PERIOD_DAILY),
                           UnitNames.PERIOD_DAILY) == idx

        # weekly
        idx_w = period_index(self.dt, UnitNames.PERIOD_WEEKLY)
        prev_w = previous_period(idx_w, UnitNames.PERIOD_WEEKLY)
        assert next_period(prev_w, UnitNames.PERIOD_WEEKLY) == idx_w

        # monthly
        idx_m = period_index(self.dt, UnitNames.PERIOD_MONTHLY)
        assert idx_m == (2025, 7)
        assert previous_period(idx_m, UnitNames.PERIOD_MONTHLY) == (2025, 6)
        assert next_period(idx_m, UnitNames.PERIOD_MONTHLY) == (2025, 8)

    def test_streak_calculations(self):
        # build a dict of 5 consecutive days, then a gap, then 2 more
        counts = {}
        for i in range(5):
            counts[(2025, 7, 13 + i)] = 1
        counts[(2025, 7, 20)] = 1
        counts[(2025, 7, 21)] = 1

        # longest overall is max(5, 2) → 5
        assert longest_streak(counts, UnitNames.PERIOD_DAILY, required=1) == 5
        # if requirement is 2 per period, none qualify
        assert longest_streak(counts, UnitNames.PERIOD_DAILY, required=2) == 0

    def test_streak_analyse(self):
        # assert current_streak(counts, UnitNames.PERIOD_DAILY, required=1) == 5
        habit_name = "water"
        length, period_type = streak_analyse(self.db, habit_name)
        assert length == 0
        water_id = find_counter_by_name(self.db, habit_name)

        period_count = get_period_count(self.db, water_id)

        for i in range(period_count):
            increment_counter(self.db, water_id, datetime(2025, 7, 17, 10 + i, 0, 0))

        length, period_type = streak_analyse(self.db, habit_name)

        assert length == 1





