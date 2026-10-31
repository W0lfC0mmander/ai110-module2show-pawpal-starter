from datetime import date, datetime, time

import streamlit as st

from pawpal_system import Owner, PawPalsApp, Priority, Task, TaskStatus

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("Plan and schedule care tasks for your pets.")

if "pawpal_app" not in st.session_state:
    pawpal_app = PawPalsApp(Owner(id=1, name="Jordan"))
    pawpal_app.add_pet("Mochi", "dog")
    st.session_state.pawpal_app = pawpal_app

pawpal_app: PawPalsApp = st.session_state.pawpal_app
owner = pawpal_app.current_owner
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Adding a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    try:
        pet = pawpal_app.add_pet(new_pet_name, new_pet_species)
    except ValueError as error:
        st.error(str(error))
    else:
        st.success(f"Added {pet.name} ({pet.species}).")

st.subheader("Add a Care Task")
if not owner.pets:
    st.info("Add a pet before creating care tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        selected_pet_id = st.selectbox(
            "Pet",
            options=[pet.id for pet in owner.pets],
            format_func=lambda pet_id: owner.find_pet(pet_id).name,
        )
        task_title = st.text_input("Task title")
        duration_minutes = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
        priority_value = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        if not task_title.strip():
            st.error("Task title cannot be empty.")
        else:
            pet = owner.find_pet(selected_pet_id)
            next_task_id = max(
                (
                    task.id
                    for existing_pet in owner.pets
                    for task in existing_pet.care_tasks
                ),
                default=0,
            ) + 1
            task = Task(
                id=next_task_id,
                title=task_title.strip(),
                duration_minutes=int(duration_minutes),
                priority=Priority(priority_value),
                status=TaskStatus.SCHEDULED,
            )
            try:
                pet.add_care_task(task)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Added {task.title} for {pet.name}.")

if owner.pets and any(pet.care_tasks for pet in owner.pets):
    st.markdown("### Care Tasks")
    st.table(
        [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority.value,
                "Status": task.status.value,
            }
            for pet, task in pawpal_app.schedule_service.get_tasks(owner)
        ]
    )

st.divider()
st.subheader("Scheduling a Task")
available_tasks = pawpal_app.schedule_service.organize_tasks(owner)
if not available_tasks:
    st.info("Add a care task to schedule it.")
else:
    with st.form("schedule_task_form"):
        selected_task_index = st.selectbox(
            "Care task",
            options=range(len(available_tasks)),
            format_func=lambda index: (
                f"{available_tasks[index][0].name} — "
                f"{available_tasks[index][1].title} "
                f"({available_tasks[index][1].duration_minutes} min)"
            ),
        )
        scheduled_date = st.date_input("Date", value=date.today())
        scheduled_time = st.time_input("Start time", value=time(8, 0))
        schedule_submitted = st.form_submit_button("Schedule task")

    if schedule_submitted:
        pet, task = available_tasks[selected_task_index]
        try:
            scheduled_task = pawpal_app.schedule_task(
                pet.id,
                task,
                datetime.combine(scheduled_date, scheduled_time),
            )
        except (LookupError, ValueError) as error:
            st.error(str(error))
        else:
            st.success(
                f"Scheduled {task.title} for {pet.name} at "
                f"{scheduled_task.start_at:%Y-%m-%d %H:%M}."
            )
            for warning in scheduled_task.warnings:
                st.warning(warning)

st.markdown("### Daily Schedule")
view_date = st.date_input("View schedule for", value=date.today(), key="view_date")
scheduled_tasks = pawpal_app.schedule_service.get_todays_tasks(owner, view_date)
if scheduled_tasks:
    st.table(
        [
            {
                "Time": scheduled_task.start_at.strftime("%H:%M"),
                "Pet": scheduled_task.pet.name,
                "Task": scheduled_task.task.title,
                "Duration (min)": scheduled_task.task.duration_minutes,
            }
            for scheduled_task in scheduled_tasks
        ]
    )
else:
    st.info("No tasks are scheduled for this date.")
