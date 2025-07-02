from db import get_counter_data

def calculate_count(db, counter):
    data = get_counter_data(db, counter)
    return len(data)
