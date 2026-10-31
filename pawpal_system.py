from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETE = "complete"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: int
    title: str
    duration_minutes: int
    priority: Priority
    status: TaskStatus
    description: str = field(default="", kw_only=True)
    frequency: str = field(default="once", kw_only=True)

    def mark_complete(self) -> None:
        """Mark the task as complete."""
        self.status = TaskStatus.COMPLETE

    @property
    def completed(self) -> bool:
        """Return whether the task is complete."""
        return self.status is TaskStatus.COMPLETE


CareTask = Task


@dataclass
class Walk(Task):
    location: str
    distance_km: float

    def set_location(self, location: str) -> None:
        """Update the walk location after validating it."""
        if not location.strip():
            raise ValueError("Walk location cannot be empty.")
        self.location = location.strip()


@dataclass
class Pet:
    id: int
    name: str
    species: str
    birth_date: date
    care_tasks: list[CareTask] = field(default_factory=list)

    def add_care_task(self, task: CareTask) -> None:
        """Add a care task to the pet if it is not already present."""
        if any(existing.id == task.id for existing in self.care_tasks):
            raise ValueError(f"Task id {task.id} is already registered to this pet.")
        self.care_tasks.append(task)

    def get_care_tasks(self) -> list[CareTask]:
        """Return a copy of the pet's care tasks."""
        return list(self.care_tasks)


@dataclass
class Owner:
    id: int
    name: str
    pets: list[Pet] = field(default_factory=list)
    daily_schedules: dict[date, DailySchedule] = field(default_factory=dict)
    daily_time_budget_minutes: Optional[int] = None
    preferred_start_time: Optional[time] = None

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with the owner if it is not already present."""
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError(f"Pet id {pet.id} is already registered to this owner.")
        self.pets.append(pet)

    def get_all_tasks(self) -> list[CareTask]:
        """Return every care task assigned to the owner's pets."""
        return [task for pet in self.pets for task in pet.care_tasks]

    def find_pet(self, pet_id: int) -> Pet:
        """Return the pet matching the provided ID."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        raise LookupError(f"Pet id {pet_id} was not found.")

    def get_schedule_for(self, day: date) -> Optional[DailySchedule]:
        """Return the schedule for the given day if it exists."""
        return self.daily_schedules.get(day)

    def get_or_create_schedule(self, day: date) -> DailySchedule:
        """Return the daily schedule for the date, creating one if needed."""
        schedule = self.get_schedule_for(day)
        if schedule is None:
            schedule = DailySchedule(day)
            self.daily_schedules[day] = schedule
        return schedule


@dataclass
class ScheduledTask:
    pet: Pet
    task: CareTask
    start_at: datetime
    notes: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def end_at(self) -> datetime:
        """Return the scheduled task's end time."""
        return self.start_at + timedelta(minutes=self.task.duration_minutes)

    def reschedule(self, start_at: datetime) -> None:
        """Move the task to a new time on the same day."""
        if start_at.date() != self.start_at.date():
            raise ValueError("A scheduled task must remain on the same day.")
        if self.task.duration_minutes <= 0:
            raise ValueError("Care task duration must be greater than zero.")
        self.start_at = start_at

    def is_for(self, day: date) -> bool:
        """Return whether the task occurs on the given day."""
        return self.start_at.date() == day


@dataclass
class DailySchedule:
    date: date
    tasks: list[ScheduledTask] = field(default_factory=list)

    def add_task(
        self, task: ScheduledTask, *, allow_conflicts: bool = False
    ) -> None:
        """Add a scheduled task to the daily schedule if it fits."""
        if not task.is_for(self.date) or task.end_at.date() != self.date:
            raise ValueError("Scheduled task date must match the daily schedule.")
        if task.end_at <= task.start_at:
            raise ValueError("Scheduled task end time must be after its start time.")
        if not allow_conflicts and not self.is_available(task.start_at, task.end_at):
            raise ValueError("Scheduled task overlaps an existing task or has invalid times.")
        self.tasks.append(task)
        self.tasks.sort(key=lambda scheduled_task: scheduled_task.start_at)

    def is_available(self, start_at: datetime, end_at: datetime) -> bool:
        """Return whether the requested time block is free in the schedule."""
        if start_at.date() != self.date or end_at.date() != self.date:
            return False
        if (start_at.utcoffset() is None) != (end_at.utcoffset() is None):
            raise ValueError("Cannot compare timezone-aware and naive datetimes.")
        if end_at <= start_at:
            return False
        for task in self.tasks:
            if (task.start_at.utcoffset() is None) != (start_at.utcoffset() is None):
                raise ValueError("Cannot compare timezone-aware and naive datetimes.")
            if start_at < task.end_at and task.start_at < end_at:
                return False
        return True

    def get_tasks_for(self, day: date) -> list[ScheduledTask]:
        """Return all scheduled tasks for the given day."""
        return list(self.tasks) if day == self.date else []

    def get_todays_tasks(self, today: date) -> list[ScheduledTask]:
        """Return the tasks scheduled for today."""
        return self.get_tasks_for(today)


class Scheduler:
    def get_tasks(self, owner: Owner) -> list[tuple[Pet, CareTask]]:
        """Return all pet-task pairs owned by the provided owner."""
        return [
            (pet, task)
            for pet in owner.pets
            for task in pet.get_care_tasks()
        ]

    def filter_tasks(
        self,
        owner: Owner,
        status: Optional[TaskStatus] = None,
        pet_name: Optional[str] = None,
    ) -> list[tuple[Pet, CareTask]]:
        """Return owner tasks matching the provided status and/or pet name."""
        normalized_pet_name = (
            pet_name.strip().casefold() if pet_name is not None else None
        )
        return [
            (pet, task)
            for pet, task in self.get_tasks(owner)
            if (status is None or task.status is status)
            and (
                normalized_pet_name is None
                or pet.name.strip().casefold() == normalized_pet_name
            )
        ]

    def organize_tasks(self, owner: Owner) -> list[tuple[Pet, CareTask]]:
        """Return all scheduled tasks ordered by priority."""
        priority_order = {
            Priority.HIGH: 0,
            Priority.MEDIUM: 1,
            Priority.LOW: 2,
        }
        tasks = [
            (pet, task)
            for pet, task in self.get_tasks(owner)
            if task.status is TaskStatus.SCHEDULED
        ]
        return sorted(tasks, key=lambda item: priority_order[item[1].priority])

    def complete_task(
        self, owner: Owner, scheduled_task: ScheduledTask
    ) -> Optional[ScheduledTask]:
        """Complete an occurrence and schedule the next daily or weekly one."""
        pet = scheduled_task.pet
        task = scheduled_task.task
        schedule = owner.get_schedule_for(scheduled_task.start_at.date())
        if not any(owned_pet is pet for owned_pet in owner.pets):
            raise ValueError("Cannot complete a task for a pet not owned by this owner.")
        if not any(existing_task is task for existing_task in pet.care_tasks):
            raise ValueError("Care task must belong to the scheduled pet.")
        if schedule is None or not any(
            existing is scheduled_task for existing in schedule.tasks
        ):
            raise ValueError("Scheduled task is not registered in the owner's schedule.")
        if task.completed:
            return None

        interval_days = {"daily": 1, "weekly": 7}.get(
            task.frequency.strip().casefold()
        )
        if interval_days is None:
            task.mark_complete()
            return None

        next_start_at = scheduled_task.start_at + timedelta(days=interval_days)
        next_task_id = max((item.id for item in owner.get_all_tasks()), default=0) + 1
        next_task = replace(task, id=next_task_id, status=TaskStatus.SCHEDULED)
        pet.add_care_task(next_task)
        try:
            next_occurrence = self.schedule_task(
                owner, pet, next_task, next_start_at, scheduled_task.notes
            )
        except ValueError:
            pet.care_tasks.remove(next_task)
            raise

        task.mark_complete()
        return next_occurrence

    def schedule_task(
        self,
        owner: Owner,
        pet: Pet,
        task: CareTask,
        start_at: datetime,
        notes: str = "",
    ) -> ScheduledTask:
        """Create and register a scheduled task for the specified pet."""
        if not any(owned_pet is pet for owned_pet in owner.pets):
            raise ValueError("Cannot schedule a task for a pet not owned by this owner.")
        if not any(existing_task is task for existing_task in pet.care_tasks):
            raise ValueError("Care task must belong to the selected pet.")
        if task.duration_minutes <= 0:
            raise ValueError("Care task duration must be greater than zero.")

        schedule = owner.get_schedule_for(start_at.date())
        if schedule is None:
            schedule = DailySchedule(start_at.date())
        end_at = start_at + timedelta(minutes=task.duration_minutes)
        if end_at.date() != start_at.date():
            raise ValueError("Scheduled task must end on the same day it starts.")
        warnings = self.detect_conflicts(owner, start_at, end_at)

        budget = owner.daily_time_budget_minutes
        if budget is not None and budget < 0:
            raise ValueError("The owner's daily time budget cannot be negative.")
        scheduled_minutes = sum(item.task.duration_minutes for item in schedule.tasks)
        if budget is not None and scheduled_minutes + task.duration_minutes > budget:
            raise ValueError("The task exceeds the owner's daily time budget.")

        scheduled_task = ScheduledTask(pet, task, start_at, notes, warnings)
        owner.daily_schedules[start_at.date()] = schedule
        schedule.add_task(scheduled_task, allow_conflicts=True)
        return scheduled_task

    def get_todays_tasks(self, owner: Owner, today: date) -> list[ScheduledTask]:
        """Return the scheduled tasks for the given day."""
        schedule = owner.get_schedule_for(today)
        return [] if schedule is None else schedule.get_tasks_for(today)

    def check_availability(
        self, schedule: DailySchedule, start_at: datetime, end_at: datetime
    ) -> bool:
        """Return whether the requested slot does not overlap existing tasks."""
        return schedule.is_available(start_at, end_at)

    def detect_conflicts(
        self, owner: Owner, start_at: datetime, end_at: datetime
    ) -> list[str]:
        """Return warnings for tasks that overlap the requested time range."""
        schedule = owner.get_schedule_for(start_at.date())
        if schedule is None:
            return []

        warnings = []
        for existing in schedule.tasks:
            if (existing.start_at.utcoffset() is None) != (start_at.utcoffset() is None):
                raise ValueError("Cannot compare timezone-aware and naive datetimes.")
            if start_at < existing.end_at and existing.start_at < end_at:
                warnings.append(
                    f"Overlaps {existing.pet.name}'s task "
                    f"'{existing.task.title}' ({existing.start_at:%H:%M}-"
                    f"{existing.end_at:%H:%M})."
                )
        return warnings


ScheduleService = Scheduler


class PawPalsApp:
    def __init__(
        self, current_owner: Owner, schedule_service: Optional[Scheduler] = None
    ) -> None:
        """Initialize the app with an owner and a scheduler."""
        self.current_owner = current_owner
        self.schedule_service = (
            schedule_service if schedule_service is not None else Scheduler()
        )

    def add_pet(self, name: str, species: str) -> Pet:
        """Create and register a new pet for the current owner."""
        if not name.strip():
            raise ValueError("Pet name cannot be empty.")
        if not species.strip():
            raise ValueError("Pet species cannot be empty.")
        pet_id = max((pet.id for pet in self.current_owner.pets), default=0) + 1
        pet = Pet(pet_id, name.strip(), species.strip(), date.today())
        self.current_owner.add_pet(pet)
        return pet

    def schedule_task(
        self,
        pet_id: int,
        task: CareTask,
        start_at: datetime,
        notes: str = "",
    ) -> ScheduledTask:
        """Schedule a care task for the selected pet using the app's scheduler."""
        pet = self.current_owner.find_pet(pet_id)
        return self.schedule_service.schedule_task(
            self.current_owner, pet, task, start_at, notes
        )

    def get_todays_tasks(self) -> list[ScheduledTask]:
        """Return the tasks scheduled for today."""
        return self.schedule_service.get_todays_tasks(
            self.current_owner, date.today()
        )