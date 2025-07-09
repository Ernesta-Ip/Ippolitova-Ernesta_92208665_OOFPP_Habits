from counter import Counter
from db import *
from analyse import *

class TestCounter:

    def setup_method(self):
        self.db = get_db("test.db")
        add_counter(self.db, "test_counter", "test_description", 1, 1)
        increment_counter(self.db, "test_counter", "2025-07-07 08:08:08")
        increment_counter(self.db, "test_counter", "2025-07-08 08:08:08")
        increment_counter(self.db, "test_counter", "2025-07-09 08:08:08")
        increment_counter(self.db, "test_counter", "2025-07-09 08:08:08")

    def test_counter(self):
        counter = Counter("test_counter_1", "test_description_1", 1, 1)
        counter.store(self.db)

    def test_db_counter(self):
        data = get_counter_data(self.db, "test_counter")
        assert len(data) == 4

        count = count_events(self.db, "test_counter")
        assert count == 4

    def teardown_method(self):
        import os
        os.remove("test.db")

