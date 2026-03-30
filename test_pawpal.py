import uuid
from datetime import date

import pytest

from pawpal_system import Pet, Task, Priority


def test_task_completion_mark_complete_sets_completed_true():
    task = Task(
        id=uuid.uuid4(),
        title="Test Task",
        duration_min=10,
        priority=Priority.MEDIUM,
        type="test",
    )

    assert not task.completed
    task.mark_complete()
    assert task.completed


def test_pet_add_task_increases_task_count():
    pet = Pet(id=uuid.uuid4(), name="Fluffy", species="cat", age=3)
    assert len(pet.get_tasks()) == 0

    task = Task(
        id=uuid.uuid4(),
        title="Feed",
        duration_min=15,
        priority=Priority.HIGH,
        type="feeding",
    )

    pet.add_task(task)
    assert len(pet.get_tasks()) == 1
    assert pet.get_tasks()[0] is task
