# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The UML draft makes the initial design more concrete. `Owner` manages `Pet` objects, and each pet has `CareTask` objects; `Walk` is a specialized care task. `ScheduleService` is responsible for scheduling walks and checking availability, while a `DailySchedule` contains `ScheduledTask` entries that associate a care task with its start and end times. `PawPalsApp` acts as the entry point for managing pets and accessing schedule features. This is a proposed design captured in the UML, not functionality implemented in the starter app.

**b. Design changes**

I changed the model and UML so an `Owner` can look up per-day `DailySchedule` objects, and each `ScheduledTask` links to both its `CareTask` and the `Pet` receiving that care. The scheduling service now accepts any care task, checks availability against the relevant day's schedule, rejects overlapping or over-budget tasks, and returns tasks for an explicit date. A scheduled task's end time is derived from its start time and duration, avoiding inconsistent start/end values. The owner model also has a daily time budget and preferred start time. This is still a basic single-task scheduling path—not an automatic priority-based planner—and the Streamlit UI does not yet collect the owner settings or call the backend.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The project calls for considering time, task priority, and owner preferences. The starter UI currently captures each task's title, duration, and priority, but there is no scheduler yet and no inputs for a daily time limit or preferences. For a first version, I would prioritize essential/high-priority tasks while ensuring selected tasks fit within the available time; preferences could be considered after those requirements.

**b. Tradeoffs**

A reasonable first-version tradeoff would be to favor high-priority tasks over fitting every task into the plan. This helps make sure essential care is scheduled when the owner's time is limited, although lower-priority tasks may be left out. This is a proposed policy, not behavior implemented in the current starter app.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI in this interaction to review the project files and help draft this reflection. Asking it to compare the reflection questions with the app, README, UML, and AI interaction log was useful for grounding the answers in what the project actually contains.

**b. Judgment and verification**

I did not treat a possible description of the scheduler as implemented behavior. I checked `app.py` and confirmed that its “Generate schedule” button still displays a “Not implemented yet” message, and the UML diagram still contains placeholder classes. That verification kept the reflection from claiming that scheduling logic or tests already exist.

---

## 4. Testing and Verification

**a. What you tested**

The current project files do not include scheduler logic or tests, so I have not verified scheduling behaviors. Before calling the project complete, I would test that high-priority tasks are favored, tasks that exceed the time budget are handled predictably, and a valid plan is displayed when there are no tasks or when all tasks fit.

**b. Confidence**

I have low confidence in scheduler correctness because the scheduler has not been implemented or tested yet. Next, I would test an empty task list, a single task, tasks with different priorities, tasks that exactly use or exceed the available time, and ties in priority.

---

## 5. Reflection

**a. What went well**

The starter app provides a clear scenario and a working place to begin building the user interface. Reviewing the requirements alongside the code also made it clear which inputs and behaviors still need to be added.

**b. What you would improve**

I would implement the owner, pet, and care-task models, add inputs for the daily time budget and relevant preferences, and connect a scheduler to the Streamlit interface. I would also replace the placeholder UML with a diagram matching the implemented classes and add focused tests for the scheduling rules.

**c. Key takeaway**

My key takeaway is to distinguish planned behavior from implemented behavior. A clear design and UI are useful starting points, but the scheduler needs explicit rules and tests before I can claim that it produces a correct plan.
