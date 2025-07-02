# main.py
import questionary
from db import get_db, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
from counter import Counter
from analyse import analyse_counters

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

        if choice == "Create":
            name = questionary.text("What is the name of the counter?").ask()
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

            counter = Counter(name, desc, period_choice, period_count)
            counter.store(db)
            print(f" Counter '{name}' created: {period_count}× per {unit}.")

        elif choice == "Increment":
            name = questionary.text("What is the name of the counter?").ask()
            counter = Counter(name, description="", period_type=0, period_count=0)
            counter.increment()
            counter.add_event(db)
            print(f"➕ Incremented '{name}'.")

        elif choice == "Analyse":
            # ask which kind of analysis
            analysis = questionary.select("What analysis would you like?",
                choices= [
                    questionary.Choice("Count all events of a habit", "count"),
                    questionary.Choice("List all habits", "list_all"),
                    questionary.Choice("Group by periodicity","group_by_period_type"),
                    ]
                    ).ask()

            if analysis == "count":
                name = questionary.text("Name of the counter to count:").ask()
                cnt = analyse_counters(db, "count", counter_name=name)
                print(f" ➤ '{name}' has been incremented {cnt} times.")

            elif analysis == "list_all":
                all_names = analyse_counters(db, "list_all")
                print(" ➤ Currently tracked habits:")
                for n in all_names:
                    print(f"   • {n}")

            elif analysis == "group_by_period_type":
                groups = analyse_counters(db, "group_by_period_type")
                print(" ➤ Habits grouped by periodicity:")
                for period_name, names in groups.items():
                    print(f"   {period_name.capitalize()}:")
                    for n in names:
                        print(f"     • {n}")

if __name__ == "__main__":
    cli()
