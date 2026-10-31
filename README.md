# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Sample terminal output from `python main.py`:

```
Today's Schedule
08:00 - Mochi: Morning walk (30 min)
09:00 - Pip: Breakfast (15 min)
17:00 - Mochi: Evening feeding (10 min)
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The tests cover task completion and pet task management, scheduling and filtering,
priority ordering, recurring tasks, conflict warnings, schedule validation and
daily time budgets, and the app's pet and schedule helpers.

Successful test run:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\rolan\Codepath_Assignments\PawPals\ai110-module2show-pawpal-starter
plugins: anyio-4.12.1
collected 16 items

tests\test_pawpal.py ..                                                  [ 12%]
tests\test_pawpal_scheduling.py ..............                           [100%]

============================== 16 passed in 0.06s ==============================
```

## 📐 Smarter Scheduling

PawPal+ provides these scheduling behaviors through `Scheduler` (also available as
`ScheduleService`):

| Feature | Method(s) | Behavior |
|---------|-----------|----------|
| Task sorting | `Scheduler.organize_tasks` | Returns scheduled tasks across all pets, ordered by high, medium, then low priority. Tasks with equal priority retain their original pet/task order. |
| Task filtering | `Scheduler.filter_tasks` | Filters all owner tasks by status, pet name, or both. Pet names are trimmed and compared without regard to case; when both filters are provided, both must match. With no filters, all tasks are returned. |
| Conflict detection and warnings | `Scheduler.detect_conflicts`, `Scheduler.schedule_task`, `ScheduledTask.warnings` | Detects strictly overlapping time ranges on the same day (touching endpoints are not conflicts) and records a warning naming each conflicting pet, task, and time range. Conflicts do not prevent scheduling. The Streamlit UI displays the warnings after scheduling. Comparing timezone-aware and timezone-naive times raises a `ValueError`. |
| Availability checks | `Scheduler.check_availability`, `DailySchedule.is_available` | Reports whether a time range is free in the daily schedule. |
| Scheduling validation and daily time budget | `Scheduler.schedule_task` | Requires the pet and task to belong to the owner, requires a positive duration, and disallows tasks that run past midnight. If adding a task would exceed the owner's configured daily time budget, scheduling is rejected with a `ValueError`. |
| Recurring tasks | `Task.frequency`, `Scheduler.complete_task` | Completing a task with `frequency="daily"` or `"weekly"` (case-insensitive) creates and schedules a new task for the next day or week at the same time, preserving its task details and notes. The completed occurrence is marked complete. Other frequency values do not create another occurrence. |
| Daily schedule ordering and lookup | `DailySchedule.add_task`, `Scheduler.get_todays_tasks` | Keeps a day's scheduled tasks ordered by start time and returns the tasks for the requested date. |

## 📸 Demo Walkthrough

The Streamlit app lets an owner manage pets and care tasks in one place. Update
the owner name, add pets by name and species, and create care tasks with a title,
duration, and priority. The Care Tasks table can be filtered by status and pet;
scheduled tasks are displayed in high-, medium-, then low-priority order.

Try this example workflow:

1. Start the interface with `streamlit run app.py`. The app opens with Mochi
   already added as a dog; use **Adding a Pet** to add another pet, such as Pip.
2. Under **Add a Care Task**, choose a pet, enter a task title and duration,
   select a priority, and click **Add task**. Repeat to add several tasks.
3. Use the Care Tasks filters to view tasks by status, pet, or both.
4. Under **Scheduling a Task**, choose a care task, date, and start time, then
   click **Schedule task**. The app confirms the scheduled time and shows any
   conflict warnings.
5. In **Daily Schedule**, choose the date to see its tasks in start-time order,
   along with each task's end time, pet, duration, and priority.

The scheduler orders tasks in the daily schedule chronologically and task lists
by priority (high, medium, then low). It detects overlapping time ranges and
displays a warning naming the conflicting task, but still allows the task to be
scheduled. Tasks whose time ranges only touch at an endpoint are not conflicts.

Running `python main.py` prints the following terminal example. The schedule
uses today's date, which is not printed:

```text
Warning: Overlaps Pip's task 'Breakfast' (08:00-08:15).
Today's Schedule
08:00 - Pip: Breakfast (15 min)
08:00 - Mochi: Morning walk (30 min)
17:00 - Mochi: Evening feeding (10 min)

Active Tasks by Priority
Mochi: Morning walk (high)
Pip: Breakfast (medium)
Mochi: Evening feeding (low)

Completed Tasks
Pip: Nail trim

Tasks for Mochi
Mochi: Evening feeding (scheduled)
Mochi: Morning walk (scheduled)
```
