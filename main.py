# main.py
import questionary
from db import get_db, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
from counter import Counter
from analyse import analyse_counters, UNIT_NAMES

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

def cli():
    db = get_db()
    questionary.confirm("Are you ready?").ask()

    stop = False
    while not stop:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Create", "Complete the Task", "Analyse", "Exit"]
        ).ask()

        if choice == "Exit":
            print("Bye!")
            break

        if choice == "Create":
            name = questionary.text("What is the name of the habit?").ask()
            desc = questionary.text("What is the description of the habit?").ask()

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
            print(f" Habit '{name}' created: {period_count}× per {unit}.")

        elif choice == "Complete the Task":
            name = questionary.text("What is the name of the habit?").ask()
            counter = Counter(name, description="", period_type=0, period_count=0)
            counter.increment()
            counter.add_event(db)
            print(f"➕ completed '{name}'.")

        elif choice == "Analyse":
            # ask which kind of analysis
            analysis = questionary.select("What analysis would you like?",
                choices= [
                    questionary.Choice("Count all events of a habit", "count"),
                    questionary.Choice("List all habits", "list_all"),
                    questionary.Choice("Group by periodicity","group_by_period_type"),
                    questionary.Choice("Streak length", "streak"),
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


            elif analysis == "streak":
                which = questionary.select("Current or longest streak?", choices=["current", "longest"]).ask()

                if which == "current":
                    # Streak for the only one habit
                    name = questionary.text("Name of the habit:").ask()
                    length = analyse_counters(db, "streak", counter_name=name, streak_type="current")
                    period_type = get_period_type_for(name, db)
                    unit = UNIT_NAMES.get(period_type, "period")
                    print(f" ➤ Current {unit}-streak for '{name}': {length}")

                else:
                    # Scan all habits for their longest-streak
                    habits = analyse_counters(db, "list_all")
                    best = {"name": None, "length": 0, "period_type": None}
                    for name in habits:
                        length = analyse_counters(
                            db, "streak",
                            counter_name=name,
                            streak_type="longest"
                        )
                        if length > best["length"]:
                            best.update({
                                "name": name,
                                "length": length,
                                "period_type": get_period_type_for(name, db)
                            })

                    if best["name"] is None:
                        print(" ➤ No habits found.")

                    else:
                        unit = UNIT_NAMES.get(best["period_type"], "period")
                        print(
                            f" ➤ Longest streak overall: "
                            f"'{best['name']}' with a {best['length']}-{unit}-streak."
                        )

if __name__ == "__main__":
    cli()
