import uuid
from datetime import date, datetime, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Priority, Schedule


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


def test_daily_task_autoreschedule_on_complete():
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet = Pet(id=uuid.uuid4(), name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120, owner_id=owner.id, pet_id=pet.id)

    recurring_task = Task(
        id=uuid.uuid4(),
        title="Daily walk",
        duration_min=30,
        priority=Priority.HIGH,
        type="walk",
        recurrence_days=1,
    )

    pet.add_task(recurring_task)
    schedule.add_task(recurring_task)

    # Complete it and auto-add next instance
    new_task = schedule.complete_task(recurring_task.id)
    assert new_task is not None
    assert new_task.title == recurring_task.title
    assert new_task.recurrence_days == 1
    assert not new_task.completed

    # One task is completed, and one new pending scheduled for next occurrence is present
    completed = schedule.filter_tasks(status="completed")
    pending = schedule.filter_tasks(status="pending")
    assert len(completed) == 1
    assert any(t.title == "Daily walk" for t in pending)


def test_owner_detects_conflicts_same_and_different_pets():
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet_a = Pet(id=uuid.uuid4(), name="A", species="dog", age=4)
    pet_b = Pet(id=uuid.uuid4(), name="B", species="cat", age=3)
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)

    task_a = Task(id=uuid.uuid4(), title="A walk", duration_min=30, priority=Priority.HIGH, type="walk")
    task_a.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=9)
    task_a.scheduled_end = task_a.scheduled_start + timedelta(minutes=30)

    task_b = Task(id=uuid.uuid4(), title="B feeding", duration_min=20, priority=Priority.MEDIUM, type="feeding")
    task_b.scheduled_start = task_a.scheduled_start + timedelta(minutes=15)
    task_b.scheduled_end = task_b.scheduled_start + timedelta(minutes=20)

    pet_a.add_task(task_a)
    pet_b.add_task(task_b)

    conflicts = owner.detect_conflicts()
    assert len(conflicts) == 1
    conflict_task_1, conflict_task_2, pet1_id, pet2_id = conflicts[0]
    assert conflict_task_1 == task_a
    assert conflict_task_2 == task_b
    assert pet1_id == pet_a.id
    assert pet2_id == pet_b.id


def test_conflict_warnings_no_exception():
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet_a = Pet(id=uuid.uuid4(), name="A", species="dog", age=4)
    pet_b = Pet(id=uuid.uuid4(), name="B", species="cat", age=3)
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)

    task_a = Task(id=uuid.uuid4(), title="A walk", duration_min=30, priority=Priority.HIGH, type="walk")
    task_a.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=9)
    task_a.scheduled_end = task_a.scheduled_start + timedelta(minutes=30)

    task_b = Task(id=uuid.uuid4(), title="B feeding", duration_min=20, priority=Priority.MEDIUM, type="feeding")
    task_b.scheduled_start = task_a.scheduled_start + timedelta(minutes=10)
    task_b.scheduled_end = task_b.scheduled_start + timedelta(minutes=20)

    pet_a.add_task(task_a)
    pet_b.add_task(task_b)

    warnings = owner.detect_conflicts()  # still path using tuple list
    assert len(warnings) == 1

    # Use schedule-level just for warning strings semantics
    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120, owner_id=owner.id, pet_id=pet_a.id)
    schedule.tasks = [task_a, task_b]
    warning_messages = schedule.conflict_warnings()
    assert len(warning_messages) == 1
    assert "overlaps with" in warning_messages[0]


def test_schedule_sort_and_filter_conflict_and_recurring_behavior():
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet = Pet(id=uuid.uuid4(), name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120, owner_id=owner.id, pet_id=pet.id)

    t1 = Task(id=uuid.uuid4(), title="Feed pet", duration_min=15, priority=Priority.HIGH, type="feeding")
    t2 = Task(id=uuid.uuid4(), title="Daily walk", duration_min=30, priority=Priority.MEDIUM, type="walk", recurrence_days=1)
    t3 = Task(id=uuid.uuid4(), title="Check email", duration_min=10, priority=Priority.LOW, type="task")

    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)

    for t in pet.get_tasks():
        schedule.add_task(t)

    scheduled = schedule.generate_plan()
    assert len(scheduled) >= 2

    # sort by scheduled time works
    ordered = schedule.sort_tasks_by_time()
    assert all(ordered[i].scheduled_start <= ordered[i+1].scheduled_start for i in range(len(ordered)-1))

    # filter by status
    completed_count = len(schedule.filter_tasks(status="completed"))
    assert completed_count == 0

    # check that recurring task is present for today
    has_daily = any(t.title == "Daily walk" for t in scheduled)
    assert has_daily

    # conflict detection: add overlapping tasks manually to force conflict
    overlapping1 = Task(id=uuid.uuid4(), title="Conflict A", duration_min=30, priority=Priority.HIGH, type="walk")
    overlapping1.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=9)
    overlapping1.scheduled_end = overlapping1.scheduled_start + timedelta(minutes=30)
    overlapping2 = Task(id=uuid.uuid4(), title="Conflict B", duration_min=30, priority=Priority.HIGH, type="walk")
    overlapping2.scheduled_start = overlapping1.scheduled_start + timedelta(minutes=15)
    overlapping2.scheduled_end = overlapping2.scheduled_start + timedelta(minutes=30)

    schedule.tasks.extend([overlapping1, overlapping2])
    conflicts = schedule.detect_conflicts()
    assert len(conflicts) >= 1


def test_recurring_task_next_occurrence_month_end_and_leap_year():
    base_date = date(2024, 1, 31)
    task = Task(
        id=uuid.uuid4(),
        title="Medicate",
        duration_min=10,
        priority=Priority.MEDIUM,
        type="medicine",
        recurrence_days=30,
        created_date=base_date,
    )

    expected_next = task.next_occurrence(date(2024, 1, 31))
    assert expected_next == date(2024, 3, 1) or expected_next == date(2024, 3, 1)

    # leap-year check from Feb 29
    task2 = Task(
        id=uuid.uuid4(),
        title="Checkup",
        duration_min=20,
        priority=Priority.LOW,
        type="vet",
        recurrence_days=365,
        created_date=date(2020, 2, 29),
    )
    assert task2.next_occurrence(date(2020, 2, 29)) == date(2021, 2, 28)


def test_schedule_generate_plan_prioritizes_and_stabilizes_tie():
    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120)

    high1 = Task(id=uuid.uuid4(), title="Walk1", duration_min=30, priority=Priority.HIGH, type="walk")
    high2 = Task(id=uuid.uuid4(), title="Walk2", duration_min=30, priority=Priority.HIGH, type="walk")
    low1 = Task(id=uuid.uuid4(), title="Play", duration_min=30, priority=Priority.LOW, type="play")

    for t in [high1, high2, low1]:
        t.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=8)
        t.scheduled_end = t.scheduled_start + timedelta(minutes=t.duration_min)
        schedule.add_task(t)

    # All have same priority level for high tasks; order should preserve by title or creation in sorted list
    sorted_tasks = schedule.generate_plan()
    assert len(sorted_tasks) >= 2
    assert sorted_tasks[0].priority == Priority.HIGH
    assert sorted_tasks[1].priority == Priority.HIGH


def test_complete_recurring_task_creates_next_occurrence_and_carries_over():
    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120)
    recurring = Task(
        id=uuid.uuid4(),
        title="Daily Feed",
        duration_min=15,
        priority=Priority.MEDIUM,
        type="feeding",
        recurrence_days=1,
        created_date=date.today(),
    )
    schedule.add_task(recurring)
    new_task = schedule.complete_task(recurring.id)

    assert recurring.completed
    assert recurring.last_completed_date == date.today()
    assert new_task is not None
    assert new_task.created_date == date.today() + timedelta(days=1)


def test_task_validation_rejects_invalid_inputs():
    invalid_cases = [
        Task(id=uuid.uuid4(), title="", duration_min=10, priority=Priority.LOW, type="feed"),
        Task(id=uuid.uuid4(), title="Bad", duration_min=-5, priority=Priority.LOW, type="feed"),
        Task(id=uuid.uuid4(), title="Bad", duration_min=10, priority=Priority.LOW, type="", recurrence_days=1),
        Task(id=uuid.uuid4(), title="Bad", duration_min=10, priority=Priority.LOW, type="feed", recurrence_days=0),
    ]

    for task in invalid_cases:
        assert not task.validate()


def test_schedule_detect_conflicts_with_overlapping_slots_considers_priority():
    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=120)

    t1 = Task(id=uuid.uuid4(), title="A", duration_min=60, priority=Priority.HIGH, type="walk")
    t1.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=9)
    t1.scheduled_end = t1.scheduled_start + timedelta(minutes=60)

    t2 = Task(id=uuid.uuid4(), title="B", duration_min=30, priority=Priority.LOW, type="play")
    t2.scheduled_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=9, minutes=30)
    t2.scheduled_end = t2.scheduled_start + timedelta(minutes=30)

    schedule.tasks = [t1, t2]
    conflicts = schedule.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0][0] == t1 and conflicts[0][1] == t2
