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
        (
            mochi,
            Task(1, "Evening feeding", 10, Priority.LOW, TaskStatus.SCHEDULED),
            time(17, 0),
        ),
        (
            pip,
            Task(2, "Breakfast", 15, Priority.MEDIUM, TaskStatus.SCHEDULED),
            time(8, 0),
        ),
        (
            mochi,
            Task(3, "Morning walk", 30, Priority.HIGH, TaskStatus.SCHEDULED),
            time(8, 0),
        ),
    ]

    scheduler = Scheduler()
    for pet, task, start_time in tasks:
        pet.add_care_task(task)
        scheduled_task = scheduler.schedule_task(
            owner, pet, task, datetime.combine(today, start_time)
        )
        for warning in scheduled_task.warnings:
            print(f"Warning: {warning}")

    pip.add_care_task(
        Task(4, "Nail trim", 10, Priority.MEDIUM, TaskStatus.COMPLETE)
    )

    print("Today's Schedule")
    for scheduled_task in scheduler.get_todays_tasks(owner, today):
        print(
            f"{scheduled_task.start_at:%H:%M} - {scheduled_task.pet.name}: "
            f"{scheduled_task.task.title} "
            f"({scheduled_task.task.duration_minutes} min)"
        )

    print("\nActive Tasks by Priority")
    for pet, task in scheduler.organize_tasks(owner):
        print(f"{pet.name}: {task.title} ({task.priority.value})")

    print("\nCompleted Tasks")
    for pet, task in scheduler.filter_tasks(owner, status=TaskStatus.COMPLETE):
        print(f"{pet.name}: {task.title}")

    print("\nTasks for Mochi")
    for pet, task in scheduler.filter_tasks(owner, pet_name="Mochi"):
        print(f"{pet.name}: {task.title} ({task.status.value})")


if __name__ == "__main__":
    main()