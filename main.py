# main.py
import questionary
from db import get_db, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
from counter import Counter
from analyse import calculate_count  # или from analyse import calculate_count, если файл так называется

def cli():
    db = get_db()
    questionary.confirm("Are you ready?").ask()

    stop = False
    while not stop:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Create", "Increment", "Analyse", "Exit"]
        ).ask()

        if choice == "Exit":
            print("Bye!")
            break

        # name of habit
        name = questionary.text("What is the name of the counter?").ask()

        if choice == "Create":
            desc = questionary.text("What is the description of the counter?").ask()

            period_choice = questionary.select(
                "Select periodicity type",
                choices=[
                    questionary.Choice("daily", value=PERIOD_DAILY),
                    questionary.Choice("weekly", value=PERIOD_WEEKLY),
                    questionary.Choice("monthly", value=PERIOD_MONTHLY),
                ]
            ).ask()

            unit = (
                "day" if period_choice == PERIOD_DAILY
                else "week" if period_choice == PERIOD_WEEKLY
                else "month"
            )

            period_count = int(questionary.text(
                f"How many times per {unit}?"
            ).ask())

            # Передаём все 4 аргумента!
            counter = Counter(name, desc, period_choice, period_count)
            counter.store(db)
            print(f" Counter '{name}' created: {period_count}× per {unit}.")

        elif choice == "Increment":
            counter = Counter(name, description="", period_type=0, period_count=0)
            counter.increment()
            counter.add_event(db)
            print(f"➕ Incremented '{name}'.")

        elif choice == "Analyse":
            count = calculate_count(db, name)
            print(f" {name}: has been incremented {count} times.")

if __name__ == "__main__":
    cli()
