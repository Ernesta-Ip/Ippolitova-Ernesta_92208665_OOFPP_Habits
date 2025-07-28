import questionary
import db as database
from counter import Counter, add_event, delete_event
import analyse
from datetime import datetime
from db import UnitNames

def cli():
    """Launch the interactive command-line interface for the habit tracker.

    Presents a menu of actions—Create, Delete, Complete the Task, Analyse, and Exit—
    and drives the full workflow for managing habits:
      - Create a new habit (name, description, periodicity, target count)
      - Delete an existing habit (with confirmation)
      - Record a completion event (with optional timestamp override)
      - Perform analyses (total count, list all, group by periodicity, current and longest streaks)
      - Exit the application loop

    This function will block until the user selects “Exit.”
    """

    db = database.get_db()

    #Actions with habits
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Create", "Delete", "Complete the Task", "Analyse", "Exit"]
        ).ask()
        if not choice: continue

        if choice == "Exit":
            print("Bye!")
            break

        elif choice == "Create":
                name = questionary.text("What is the name of the habit?").ask()
                if not name:
                    continue

                if database.exist(db, database.find_counter_by_name(db, name)):
                    print(f"Habit '{name}' already exists, please choose a different name.\n")
                    continue

                desc = questionary.text("What is the description of the habit?").ask()
                if not desc:
                    continue

                period_choice = questionary.select(
                        "Select periodicity type",
                        choices=[
                            questionary.Choice(UnitNames.PERIOD_DAILY.label, value=UnitNames.PERIOD_DAILY),
                            questionary.Choice(UnitNames.PERIOD_WEEKLY.label, value=UnitNames.PERIOD_WEEKLY),
                            questionary.Choice(UnitNames.PERIOD_MONTHLY.label, value=UnitNames.PERIOD_MONTHLY),
                        ]
                ).ask()

                if not period_choice:
                    continue

                unit = (
                        "day" if period_choice is UnitNames.PERIOD_DAILY
                        else "week" if period_choice is UnitNames.PERIOD_WEEKLY
                        else "month"
                )

                period_count = questionary.text(
                        f"How many times per {unit}?"
                ).ask()

                if not period_count: continue

                counter = Counter(name, desc, period_choice, int(period_count))

                database.add_counter(db, counter.name, counter.description, counter.period_type, counter.period_count)

                print(f" Habit '{name}' created: {period_count}× per {unit}.")

        elif choice == "Delete":
            habit_names = database.get_habit_names(db)

            if not habit_names:
                print("You don't have any habits yet. Please create one.\n")
                continue

            name = questionary.select(
                "Which habit do you want to delete?",
                choices=habit_names
            ).ask()
            if not name: continue

            # ask for confirmation
            confirm = questionary.confirm(
                f"Are you sure you want to delete '{name}' and all its records?"
            ).ask()
            if not confirm: continue

            if confirm:
                delete_event(db, name)
                print(f"Habit '{name}' and its history have been deleted.\n")
            else:
                print("Deletion cancelled.\n")

        elif choice == "Complete the Task":
            habit_names = database.get_habit_names(db)

            if not habit_names:
                print("You don't have any habits yet. Please create one.\n")
                continue

            name = questionary.select(
                "Which habit did you complete?",
                choices=habit_names
            ).ask()
            if not name: continue

            #setting timestamp manually

            set_timestamp_manually = questionary.confirm(
                "Do you want to set the completion timestamp manually?",
                default=False
            ).ask()

            completed_at = datetime.now()

            if set_timestamp_manually:
                while True:
                    ts_str = questionary.text(
                        "Enter timestamp (YYYY-MM-DD HH:MM:SS):",
                        default=completed_at.strftime("%Y-%m-%d %H:%M:%S")
                    ).ask()
                    if not ts_str: continue
                    try:
                        completed_at = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        print(f"'{ts_str}' is not a valid timestamp. Please use YYYY-MM-DD HH:MM:SS.\n")
                        continue
                    break
            try:
                add_event(name, db, completed_at)
            except Exception as e:
                print(f" Could not record completion for '{name}': {e}\n")
            print(f"➕ Completed '{name}' on {completed_at.strftime("%Y-%m-%d %H:%M:%S")}.\n")

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
            if not analysis: continue

            if analysis == "count":
                # Select the habit to be counted
                habit_names = database.get_habit_names(db)

                if not habit_names:
                    print("You don't have any habits yet. Please create one.\n")
                    continue

                name = questionary.select(
                    "Which habit do you want to count tasks for?",
                    choices=habit_names
                ).ask()
                if not name: continue

                cnt = analyse.count_events(db, name)
                print(f" ➤ '{name}' has been incremented {cnt} times.")

            elif analysis == "list_all":
                habit_names = database.get_habit_names(db)
                print(" ➤ Currently tracked habits:")
                for n in habit_names:
                    print(f"   • {n}")

            elif analysis == "group_by_period_type":
                groups = analyse.group_by_period_type(db)
                print(" ➤ Habits grouped by periodicity:")
                for period_enum, comma_names in groups:
                    print(f" • {UnitNames(period_enum).label}:")
                    for n in comma_names.split(","):
                        print(f"    – {n}")


            elif analysis == "streak":
                which = questionary.select("Current or longest streak?", choices=["current", "longest"]).ask()
                if not which: continue

                # fetch all habit names
                habit_names = database.get_habit_names(db)
                if not habit_names:
                    print("You don't have any habits yet. Please create one.\n")
                    continue

                if which == "current":
                    name = questionary.select(
                        "Which habit do you want the streak for?",
                        choices=habit_names
                    ).ask()
                    if not name: continue

                    length, period_type = analyse.streak_analyse(db, name)

                    unit = period_type.label
                    unit_label = unit if length == 1 else unit + "s"

                    print(
                        f"➤ You have established a current streak of "
                        f"{length} {unit_label} for '{name}'.\n"
                    )

                if which == "longest":
                    max_length = 0
                    best_habit = None
                    best_unit = "period"

                    # for each habit, compute its longest streak
                    for name in habit_names:
                        length, period_type = analyse.streak_analyse(db, name)

                        # track the overall best
                        if length > max_length:
                            max_length = length
                            best_habit = name
                            best_unit = period_type.label

                    if max_length == 0:
                        print("➤ You haven't met the requirement for any streak yet.\n")
                    else:
                        unit_label = best_unit if max_length == 1 else best_unit + "s"
                        print(
                            f"➤ Your longest streak overall is {max_length} "
                            f"{unit_label} on '{best_habit}'.\n"
                        )


if __name__ == "__main__":
    cli()
