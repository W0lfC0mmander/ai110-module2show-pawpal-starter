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


def test_scheduling_links_task_to_owner_schedule_and_pet():
    owner, pet, task = make_owner_and_task()
    start_at = datetime(2026, 10, 31, 8, 0)

    scheduled = ScheduleService().schedule_task(owner, pet, task, start_at)

    assert scheduled.pet is pet
    assert scheduled.task is task
    assert scheduled.end_at == datetime(2026, 10, 31, 8, 30)
    assert owner.get_schedule_for(start_at.date()).tasks == [scheduled]


def test_schedule_rejects_overlaps_and_tasks_on_another_day():
    owner, pet, task = make_owner_and_task()
    service = ScheduleService()
    start_at = datetime(2026, 10, 31, 8, 0)
    service.schedule_task(owner, pet, task, start_at)

    with pytest.raises(ValueError, match="overlaps"):
        service.schedule_task(owner, pet, task, datetime(2026, 10, 31, 8, 15))

    next_day_schedule = owner.get_or_create_schedule(date(2026, 11, 1))
    wrong_day_task = ScheduledTask(pet, task, start_at)
    with pytest.raises(ValueError, match="date must match"):
        next_day_schedule.add_task(wrong_day_task)


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
