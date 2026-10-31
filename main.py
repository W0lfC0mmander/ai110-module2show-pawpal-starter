from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task, TaskStatus


def main() -> None:
    today = date.today()
    owner = Owner(1, "Jordan")
    mochi = Pet(1, "Mochi", "dog", date(2020, 1, 1))
    pip = Pet(2, "Pip", "cat", date(2022, 4, 1))
    owner.add_pet(mochi)
    owner.add_pet(pip)

    tasks = [
        (mochi, Task(1, "Morning walk", 30, Priority.HIGH, TaskStatus.SCHEDULED), time(8, 0)),
        (pip, Task(2, "Breakfast", 15, Priority.MEDIUM, TaskStatus.SCHEDULED), time(9, 0)),
        (mochi, Task(3, "Evening feeding", 10, Priority.HIGH, TaskStatus.SCHEDULED), time(17, 0)),
    ]

    scheduler = Scheduler()
    for pet, task, start_time in tasks:
        pet.add_care_task(task)
        scheduler.schedule_task(owner, pet, task, datetime.combine(today, start_time))

    print("Today's Schedule")
    for scheduled_task in scheduler.get_todays_tasks(owner, today):
        print(
            f"{scheduled_task.start_at:%H:%M} - {scheduled_task.pet.name}: "
            f"{scheduled_task.task.title} "
            f"({scheduled_task.task.duration_minutes} min)"
        )


if __name__ == "__main__":
    main()