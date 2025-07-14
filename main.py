import questionary
import db as database
from counter import Counter, add_event, delete_event
import analyse
from datetime import datetime
from db import UnitNames

def cli():
    db = database.get_db()

    #Actions with habits
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Create", "Delete", "Complete the Task", "Analyse", "Exit"]
        ).ask()

        if choice == "Exit":
            print("Bye!")
            break

        # TODO: by defining four choices: Create, Delete, Complete, Analyse, the classical CRUD access to the database
        #   is used: Create, Read, Update, Delete. https://de.wikipedia.org/wiki/CRUD. This can be used to abstract/refactor
        #   the four blocks into their functions. Moreover, your db module already implements functions, using the cursor,
        #   this is a good occasion to not use this sort of low level functions within the main. This is, because it is
        #   a bad behavior to expose the underlying data source to the user directly, for security reasons.
        elif choice == "Create":
                name = questionary.text("What is the name of the habit?").ask()

                if database.exist(db, name):
                    print(f"Habit '{name}' already exists, please choose a different name.\n")
                    continue

                desc = questionary.text("What is the description of the habit?").ask()

                period_choice = questionary.select(
                        "Select periodicity type",
                        choices=[
                            questionary.Choice(UnitNames.PERIOD_DAILY.label, value=UnitNames.PERIOD_DAILY),
                            questionary.Choice(UnitNames.PERIOD_WEEKLY.label, value=UnitNames.PERIOD_WEEKLY),
                            questionary.Choice(UnitNames.PERIOD_MONTHLY.label, value=UnitNames.PERIOD_MONTHLY),
                        ]
                ).ask()

                unit = (
                        "day" if period_choice is UnitNames.PERIOD_DAILY
                        else "week" if period_choice is UnitNames.PERIOD_WEEKLY
                        else "month"
                )

                period_count = int(questionary.text(
                        f"How many times per {unit}?"
                ).ask())

                counter = Counter(name, desc, period_choice, period_count)
                counter.store(db)

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

            # ask for confirmation
            confirm = questionary.confirm(
                f"Are you sure you want to delete '{name}' and all its records?"
            ).ask()

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
            print(f"➕ Completed '{name}' on {completed_at}.\n")

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
                # Select the habit to be counted
                habit_names = database.get_habit_names(db)

                if not habit_names:
                    print("You don't have any habits yet. Please create one.\n")
                    continue

                name = questionary.select(
                    "Which habit do you want to count tasks for?",
                    choices=habit_names
                ).ask()
                cnt = analyse.count_events(db, counter_id=name)
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

                # TODO: while in former cases, your analysis_counters yields all the results, which could be printed,
                #   in the case of the current "streak" analysis you need more functions to get e.g.,
                #   period_type, unit, unit_label. Why is that?

                if which == "current":
                    # Select the habit to count the current streak
                    habit_names = database.get_habit_names(db)

                    if not habit_names:
                        print("You don't have any habits yet. Please create one.\n")
                        continue

                    name = questionary.select(
                        "Which habit do you want the streak for?",
                        choices=habit_names
                    ).ask()

                    #settings for the habit
                    period_type = analyse.get_period_type_for(db, name)
                    required = analyse.get_period_count_for(db, name)

                    #setting the dictionary
                    period_counts = {}
                    for _, ts_str in analyse.get_counter_data(db, name):
                       ts = datetime.fromisoformat(ts_str)
                       idx = analyse.period_index(ts, period_type)
                       period_counts[idx] = period_counts.get(idx, 0) + 1

                    #calculate the current streak
                    length = analyse.current_streak(period_counts, period_type, required)
                    unit = period_type.label
                    unit_label = unit if length == 1 else unit + "s"

                    print(
                        f"➤ You have established a current streak of "
                        f"{length} {unit_label} for '{name}'.\n"
                    )

                # TODO: while in former cases, your analysis_counters yields all the results, which could be printed,
                #   in the case of the longest "streak" analysis you need to call this function even twice, not to
                #   mention, that half of the evaluation happens outside of the function. Why is that?

                if which == "longest":
                    # fetch all habit names
                    habit_names = database.get_habit_names(db)

                    if not habit_names:
                        print("You don't have any habits yet. Please create one.\n")
                        continue

                    max_length = 0
                    best_habit = None
                    best_unit = "period"

                    # for each habit, compute its longest streak
                    for name in habit_names:
                        period_type = analyse.get_period_type_for(db, name)
                        required = analyse.get_period_count_for(db, name)

                        # build count-by-period for this habit
                        period_counts = {}
                        for _, ts_str in analyse.get_counter_data(db, name):
                            ts = datetime.fromisoformat(ts_str)
                            idx = analyse.period_index(ts, period_type)
                            period_counts[idx] = period_counts.get(idx, 0) + 1

                        length = analyse.longest_streak(period_counts, period_type, required)

                        # track the overall best
                        if length > max_length:
                            max_length = length
                            best_habit = name
                            best_unit = analyse.UNIT_NAMES.get(period_type, "period")

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
