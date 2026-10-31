from datetime import date, datetime
from typing import Optional

import pytest

from pawpal_system import (
    CareTask,
    Owner,
    PawPalsApp,
    Pet,
    Priority,
    Scheduler,
    ScheduledTask,
    ScheduleService,
    Task,
    TaskStatus,
)


def make_owner_and_task(budget: Optional[int] = None):
    pet = Pet(1, "Mochi", "dog", date(2020, 1, 1))
    task = CareTask(1, "Walk", 30, Priority.HIGH, TaskStatus.SCHEDULED)
    pet.add_care_task(task)
    owner = Owner(1, "Jordan", daily_time_budget_minutes=budget)
    owner.add_pet(pet)
    return owner, pet, task


def test_task_completion_and_pet_task_accessors():
    assert Task is CareTask
    task = Task(
        1,
        "Medication",
        5,
        Priority.HIGH,
        TaskStatus.SCHEDULED,
        description="Give morning medication",
        frequency="daily",
    )
    pet = Pet(1, "Mochi", "dog", date(2020, 1, 1))

    pet.add_care_task(task)
    tasks = pet.get_care_tasks()
    task.mark_complete()

    assert tasks == [task]
    assert task.completed
    assert task.status is TaskStatus.COMPLETE
    assert task.description == "Give morning medication"
    assert task.frequency == "daily"
    with pytest.raises(ValueError, match="already registered"):
        pet.add_care_task(task)


def test_owner_aggregates_tasks_and_scheduler_sorts_active_tasks_by_priority():
    assert ScheduleService is Scheduler
    owner, pet, high_priority_task = make_owner_and_task()
    second_pet = Pet(2, "Pip", "cat", date(2022, 4, 1))
    low_priority_task = CareTask(
        2, "Brush", 10, Priority.LOW, TaskStatus.SCHEDULED
    )
    completed_task = CareTask(
        3, "Feed", 5, Priority.HIGH, TaskStatus.COMPLETE
    )
    second_pet.add_care_task(low_priority_task)
    second_pet.add_care_task(completed_task)
    owner.add_pet(second_pet)
    scheduler = Scheduler()

    assert owner.get_all_tasks() == [
        high_priority_task,
        low_priority_task,
        completed_task,
    ]
    assert scheduler.organize_tasks(owner) == [
        (pet, high_priority_task),
        (second_pet, low_priority_task),
    ]


def test_scheduler_filters_tasks_by_status_and_pet_name():
    owner, pet, scheduled_task = make_owner_and_task()
    second_pet = Pet(2, "Pip", "cat", date(2022, 4, 1))
    completed_task = CareTask(2, "Feed", 5, Priority.HIGH, TaskStatus.COMPLETE)
    skipped_task = CareTask(3, "Brush", 10, Priority.LOW, TaskStatus.SKIPPED)
    second_pet.add_care_task(completed_task)
    second_pet.add_care_task(skipped_task)
    owner.add_pet(second_pet)
    scheduler = Scheduler()

    assert scheduler.filter_tasks(owner, status=TaskStatus.COMPLETE) == [
        (second_pet, completed_task)
    ]
    assert scheduler.filter_tasks(owner, pet_name="  pIp ") == [
        (second_pet, completed_task),
        (second_pet, skipped_task),
    ]
    assert scheduler.filter_tasks(
        owner, status=TaskStatus.SCHEDULED, pet_name=pet.name
    ) == [(pet, scheduled_task)]
    assert scheduler.filter_tasks(owner) == [
        (pet, scheduled_task),
        (second_pet, completed_task),
        (second_pet, skipped_task),
    ]


def test_scheduling_links_task_to_owner_schedule_and_pet():
    owner, pet, task = make_owner_and_task()
    start_at = datetime(2026, 10, 31, 8, 0)

    scheduled = ScheduleService().schedule_task(owner, pet, task, start_at)

    assert scheduled.pet is pet
    assert scheduled.task is task
    assert scheduled.end_at == datetime(2026, 10, 31, 8, 30)
    assert owner.get_schedule_for(start_at.date()).tasks == [scheduled]


@pytest.mark.parametrize(
    ("frequency", "next_start_at"),
    [
        ("daily", datetime(2026, 11, 1, 8, 0)),
        ("weekly", datetime(2026, 11, 7, 8, 0)),
    ],
)
def test_completing_recurring_task_schedules_next_occurrence(
    frequency: str, next_start_at: datetime
):
    owner, pet, _ = make_owner_and_task()
    task = CareTask(
        1,
        "Medication",
        5,
        Priority.HIGH,
        TaskStatus.SCHEDULED,
        description="Give medication",
        frequency=frequency,
    )
    pet.care_tasks[0] = task
    scheduler = Scheduler()
    occurrence = scheduler.schedule_task(
        owner, pet, task, datetime(2026, 10, 31, 8, 0), "With breakfast"
    )

    next_occurrence = scheduler.complete_task(owner, occurrence)

    assert task.status is TaskStatus.COMPLETE
    assert next_occurrence is not None
    assert next_occurrence.start_at == next_start_at
    assert next_occurrence.notes == "With breakfast"
    assert next_occurrence.task is pet.care_tasks[-1]
    assert next_occurrence.task.id == 2
    assert next_occurrence.task.title == task.title
    assert next_occurrence.task.duration_minutes == task.duration_minutes
    assert next_occurrence.task.priority is task.priority
    assert next_occurrence.task.description == task.description
    assert next_occurrence.task.frequency == frequency
    assert next_occurrence.task.status is TaskStatus.SCHEDULED
    assert owner.get_schedule_for(next_start_at.date()).tasks == [next_occurrence]


def test_completing_nonrecurring_task_does_not_create_another_instance():
    owner, pet, task = make_owner_and_task()
    scheduler = Scheduler()
    occurrence = scheduler.schedule_task(
        owner, pet, task, datetime(2026, 10, 31, 8, 0)
    )

    assert scheduler.complete_task(owner, occurrence) is None

    assert task.status is TaskStatus.COMPLETE
    assert pet.get_care_tasks() == [task]


def test_recurring_completion_succeeds_with_conflict_warning():
    owner, pet, task = make_owner_and_task()
    task.frequency = "daily"
    other_pet = Pet(2, "Pip", "cat", date(2022, 4, 1))
    conflicting_task = CareTask(2, "Feed", 10, Priority.MEDIUM, TaskStatus.SCHEDULED)
    other_pet.add_care_task(conflicting_task)
    owner.add_pet(other_pet)
    scheduler = Scheduler()
    occurrence = scheduler.schedule_task(
        owner, pet, task, datetime(2026, 10, 31, 8, 0)
    )
    scheduler.schedule_task(
        owner, other_pet, conflicting_task, datetime(2026, 11, 1, 8, 0)
    )

    next_occurrence = scheduler.complete_task(owner, occurrence)

    assert task.status is TaskStatus.COMPLETE
    assert next_occurrence is not None
    assert next_occurrence.warnings == [
        "Overlaps Pip's task 'Feed' (08:00-08:10)."
    ]
    assert len(pet.get_care_tasks()) == 2


def test_schedule_warns_for_overlaps_and_still_registers_task():
    owner, pet, task = make_owner_and_task()
    service = ScheduleService()
    start_at = datetime(2026, 10, 31, 8, 0)
    existing = service.schedule_task(owner, pet, task, start_at)
    overlapping_task = CareTask(
        2, "Breakfast", 15, Priority.MEDIUM, TaskStatus.SCHEDULED
    )
    pet.add_care_task(overlapping_task)

    scheduled_overlap = service.schedule_task(
        owner, pet, overlapping_task, datetime(2026, 10, 31, 8, 15)
    )

    assert scheduled_overlap in owner.get_schedule_for(start_at.date()).tasks
    assert scheduled_overlap.warnings == [
        "Overlaps Mochi's task 'Walk' (08:00-08:30)."
    ]
    assert service.detect_conflicts(
        owner, datetime(2026, 10, 31, 8, 15), datetime(2026, 10, 31, 8, 30)
    ) == [
        "Overlaps Mochi's task 'Walk' (08:00-08:30).",
        "Overlaps Mochi's task 'Breakfast' (08:15-08:30).",
    ]
    assert existing.warnings == []


def test_conflict_warning_identifies_overlapping_task_for_another_pet():
    owner, pet, task = make_owner_and_task()
    other_pet = Pet(2, "Pip", "cat", date(2022, 4, 1))
    other_task = CareTask(2, "Feeding", 15, Priority.MEDIUM, TaskStatus.SCHEDULED)
    other_pet.add_care_task(other_task)
    owner.add_pet(other_pet)
    service = Scheduler()
    service.schedule_task(owner, pet, task, datetime(2026, 10, 31, 8, 0))

    scheduled = service.schedule_task(
        owner, other_pet, other_task, datetime(2026, 10, 31, 8, 15)
    )

    assert scheduled.warnings == [
        "Overlaps Mochi's task 'Walk' (08:00-08:30)."
    ]
    assert owner.get_schedule_for(date(2026, 10, 31)).tasks[-1] is scheduled


def test_schedule_rejects_tasks_that_cross_midnight():
    owner, pet, task = make_owner_and_task()
    task.duration_minutes = 60
    service = Scheduler()
    next_day_schedule = owner.get_or_create_schedule(date(2026, 11, 1))
    wrong_day_task = ScheduledTask(
        pet, task, datetime(2026, 10, 31, 23, 30)
    )
    with pytest.raises(ValueError, match="date must match"):
        next_day_schedule.add_task(wrong_day_task)
    with pytest.raises(ValueError, match="same day"):
        service.schedule_task(owner, pet, task, datetime(2026, 10, 31, 23, 30))


def test_schedule_enforces_daily_time_budget():
    owner, pet, task = make_owner_and_task(budget=30)
    service = ScheduleService()
    service.schedule_task(owner, pet, task, datetime(2026, 10, 31, 8, 0))

    with pytest.raises(ValueError, match="daily time budget"):
        service.schedule_task(owner, pet, task, datetime(2026, 10, 31, 9, 0))


def test_app_schedules_tasks_and_service_queries_by_explicit_date():
    owner, pet, task = make_owner_and_task()
    service = ScheduleService()
    app = PawPalsApp(owner, service)
    scheduled = app.schedule_task(pet.id, task, datetime(2026, 10, 31, 8, 0))

    assert service.get_todays_tasks(owner, date(2026, 10, 31)) == [scheduled]
    assert service.get_todays_tasks(owner, date(2026, 11, 1)) == []


def test_app_add_pet_assigns_unique_id_and_trims_input():
    owner, _, _ = make_owner_and_task()
    pet = PawPalsApp(owner).add_pet("  Pip  ", "  cat  ")

    assert pet.id == 2
    assert pet.name == "Pip"
    assert pet.species == "cat"
    assert owner.find_pet(2) is pet
