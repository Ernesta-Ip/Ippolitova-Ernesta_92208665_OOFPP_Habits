# main.py
import questionary
from datetime import datetime
from db import get_db, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
from counter import Counter, add_event
from analyse import count_events, list_all, group_by_period_type, current_streak, longest_streak, get_period_type_for, get_period_count_for, UNIT_NAMES

def cli():
    db = get_db()

    choice = questionary.select(
        "Are you ready?",
        choices=["Yes", "No"]
    ).ask()

    if choice == "No":
        print("Bye!")
        return
    print("Welcome to the Habit Tracker!")

    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Create", "Complete the Task", "Analyse", "Exit"]
        ).ask()

        if choice == "Exit":
            print("Bye!")
            return

        if choice == "Create":
            while True:
                name = questionary.text("What is the name of the habit?").ask()
                cursor = db.cursor()
                cursor.execute("SELECT 1 FROM counter WHERE name = ?", (name,))
                if cursor.fetchone():
                    print(f"Habit '{name}' already exists, please choose a different name.\n")
                    continue
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
                break

        elif choice == "Complete the Task":
            cursor = db.cursor()
            cursor.execute("SELECT name FROM counter")
            rows = cursor.fetchall()
            habit_names = [row[0] for row in rows]

            if not habit_names:
                print("You don't have any habits yet. Please create one.\n")
                continue

            name = questionary.select(
                "Which habit did you complete?",
                choices=habit_names
            ).ask()

            set_timestamp_manually = questionary.confirm(
                "Do you want to set the completion timestamp manually?",
                default=False
            ).ask()

            if set_timestamp_manually:
                while True:
                    default_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ts_str = questionary.text(
                        "Enter timestamp (YYYY-MM-DD HH:MM:SS):",
                        default=default_ts
                    ).ask()
                    try:
                        completed_at = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        print(f"❌ '{ts_str}' is not a valid timestamp. Please use YYYY-MM-DD HH:MM:SS.\n")
                        continue
                    break
            else:
                completed_at = datetime.now().replace(microsecond=0)
            try:
                add_event(name, db, completed_at)
            except Exception as e:
                print(f"❌ Could not record completion for '{name}': {e}\n")
            else:
                ts_out = completed_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"➕ Completed '{name}' on {ts_out}.\n")

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

                # TODO: your analysis function analyse_counters seems to yield different return types. This is at least
                #   bad design. See "Clean Code, Robert C. Martin" and
                #   PEP 484, Python Type Hints: https://peps.python.org/pep-0484/
                #   the solution is quite simple here, as you even pass appropriate parameter to the function:
                #   for every kind of different analysis, define its own function

            if analysis == "count":
                    name = questionary.text("Name of the habit to count:").ask()
                    cnt = count_events(db, counter_name=name)
                    print(f" ➤ '{name}' has been incremented {cnt} times.")

            elif analysis == "list_all":
                    all_names = list_all(db)
                    print(" ➤ Currently tracked habits:")
                    for n in all_names:
                        print(f"   • {n}")

            elif analysis == "group_by_period_type":
                    groups = group_by_period_type(db)
                    print(" ➤ Habits grouped by periodicity:")
                    for period_name, names in groups.items():
                        print(f"   {period_name.capitalize()}:")
                        for n in names:
                            print(f"     • {n}")

            elif analysis == "streak":
                    which = questionary.select("Current or longest streak?", choices=["current", "longest"]).ask()

                    # TODO: while in former cases, your analysis_counters yields all the results, which could be printed,
                    #   in the case of the current "streak" analysis you need more functions to get e.g.,
                    #   period_type, unit, unit_label. Why is that?
                    if which == "current":
                        # Select the habit to count the current streak
                        cursor = db.cursor()
                        cursor.execute("SELECT name FROM counter")
                        rows = cursor.fetchall()
                        habit_names = [row[0] for row in rows]

                        if not habit_names:
                            print("You don't have any habits yet. Please create one.\n")
                            continue

                        name = questionary.select(
                            "Which habit do you want the streak for?",
                            choices=habit_names
                        ).ask()

                        #settings for the habit

                        period_type = get_period_type_for(name, db)
                        required = get_period_count_for(name, db)

                        #setting the dictionary
                        period_counts = {}
                        cursor.execute(
                            "SELECT timestamp FROM tracker WHERE counterName = ?",
                            (name,)
                        )
                        for (ts_str,) in cursor.fetchall():
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            idx = period_index(ts, period_type)
                            period_counts[idx] = period_counts.get(idx, 0) + 1

                        #calculate the current streak
                        length = current_streak(period_counts, period_type, required)
                        unit = UNIT_NAMES.get(period_type, "period")
                        unit_label = unit if length == 1 else unit + "s"

                        print(
                            f"➤ You have established a current streak of "
                            f"{length} {unit_label} for '{name}'.\n"
                        )



                    # TODO: while in former cases, your analysis_counters yields all the results, which could be printed,
                    #   in the case of the longest "streak" analysis you need to call this function even twice, not to
                    #   mention, that half of the evaluation happens outside of the function. Why is that?


                    else:
                        # Scan all habits for their longest-streak
                        habits = longest_streak(db, "list_all")
                        best = {"name": None, "length": 0, "period_type": None}
                        for name in habits:
                            length = longest_streak(
                                db,
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
