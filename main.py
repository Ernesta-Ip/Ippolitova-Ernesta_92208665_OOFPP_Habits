import questionary

import db
from db import get_db
from counter import Counter
from analyse import calculate_count

def cli():
    db = get_db()
    question = questionary.confirm("Are you ready?").ask()

    stop = False
    while not stop:

        choice = questionary.select("What would you like to do?", choices= ["Create", "Increment", "Analyse", "Exit"]).ask()

        if choice != "Exit":
            name = questionary.text("What is the name of the counter?").ask()

        if choice == "Create":
            desc = questionary.text("What is the description of the counter?").ask()
            counter = Counter(name, desc)
            counter.store(db)
        elif choice == "Increment":
            counter = Counter (name, "no description")
            counter.increment()
            counter.add_event(db)
        elif choice == "Analyse":
            count = calculate_count(db, name)
            print(f"{name}: has been incremented {count} times.")
        else:
            print("Bye!")
            stop = True

def evaluateMissingTime(habitId):
    # evaluate habit with the id habitID
    pass

def evaluateMissingTime():
    for habit in db.get_all_habits():
        evaluateMissingTime(habit["id"])
    pass

if __name__ == "__main__":
    cli()

    for habit in db.get_all_habits():
        evaluateMissingTime(habit["id"])