from datetime import date

from pawpal_system import Pet, Priority, Task, TaskStatus


def test_mark_complete_changes_task_status():
    task = Task(1, "Walk", 30, Priority.HIGH, TaskStatus.SCHEDULED)

    task.mark_complete()

    assert task.status is TaskStatus.COMPLETE


def test_adding_task_increases_pet_task_count():
    pet = Pet(1, "Mochi", "dog", date(2020, 1, 1))
    task = Task(1, "Walk", 30, Priority.HIGH, TaskStatus.SCHEDULED)
    initial_task_count = len(pet.get_care_tasks())

    pet.add_care_task(task)

    assert len(pet.get_care_tasks()) == initial_task_count + 1