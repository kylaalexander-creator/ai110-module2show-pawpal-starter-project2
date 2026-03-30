from datetime import date
import uuid

from pawpal_system import Owner, Pet, Schedule, Task, Priority


def main() -> None:
    # Create owner and pets
    owner = Owner(id=uuid.uuid4(), name="Alex", email="alex@example.com")
    pet1 = Pet(id=uuid.uuid4(), name="Buddy", species="dog", age=4)
    pet2 = Pet(id=uuid.uuid4(), name="Whiskers", species="cat", age=2)

    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # Create a daily schedule for owner and pets
    schedule = Schedule(
        id=uuid.uuid4(),
        date=date.today(),
        total_time_available=180,  # 3 hours available to schedule tasks
        owner_id=owner.id,
        pet_id=pet1.id,
    )

    # Add tasks out of chronological order to verify sorting works later
    task_out_of_order = Task(
        id=uuid.uuid4(),
        title="Evening cleanup",
        duration_min=20,
        priority=Priority.MEDIUM,
        type="cleaning",
        notes="Clear litter and food bowls",
    )
    schedule.add_task(task_out_of_order)
    pet1.add_task(task_out_of_order)

    task_urgent = Task(
        id=uuid.uuid4(),
        title="Feed Whiskers",
        duration_min=15,
        priority=Priority.HIGH,
        type="feeding",
        notes="Wet food and water",
    )
    schedule.add_task(task_urgent)
    pet2.add_task(task_urgent)

    task_midday = Task(
        id=uuid.uuid4(),
        title="Morning walk",
        duration_min=30,
        priority=Priority.HIGH,
        type="walk",
        notes="Walk Buddy around the park",
    )
    schedule.add_task(task_midday)
    pet1.add_task(task_midday)

    task_low = Task(
        id=uuid.uuid4(),
        title="Play session",
        duration_min=45,
        priority=Priority.LOW,
        type="play",
        notes="Interactive toys for both pets",
    )
    schedule.add_task(task_low)
    pet1.add_task(task_low)

    task_med = Task(
        id=uuid.uuid4(),
        title="Vet medication",
        duration_min=10,
        priority=Priority.HIGH,
        type="care",
        notes="Give daily meds to Buddy",
    )
    schedule.add_task(task_med)
    pet1.add_task(task_med)

    # Generate plan and attach to owner
    scheduled_tasks = schedule.generate_plan()
    owner.set_schedule(schedule)

    # Print today's schedule
    print("Today's Schedule")
    print("===============")
    print(owner.get_schedule().explain())

    # Verify sorting by scheduled start time
    print("\nSorted tasks by scheduled time:")
    sorted_tasks = schedule.sort_tasks_by_time()
    for t in sorted_tasks:
        print(f"- {t.title}: {t.scheduled_start.strftime('%H:%M')} - {t.scheduled_end.strftime('%H:%M')} ({t.priority.name})")

    # Add explicit conflict scenario: two tasks overlap by schedule window
    conflict1 = Task(
        id=uuid.uuid4(),
        title="Overlap walk",
        duration_min=30,
        priority=Priority.HIGH,
        type="walk",
    )
    conflict2 = Task(
        id=uuid.uuid4(),
        title="Overlap vet",
        duration_min=30,
        priority=Priority.MEDIUM,
        type="care",
    )

    # Set both at same exact time so conflict should be detected
    from datetime import datetime, time
    fixed_start = datetime.combine(date.today(), time(hour=8, minute=0))
    conflict1.scheduled_start = fixed_start
    conflict1.scheduled_end = fixed_start + timedelta(minutes=30)
    conflict2.scheduled_start = fixed_start
    conflict2.scheduled_end = fixed_start + timedelta(minutes=30)

    schedule.tasks.extend([conflict1, conflict2])

    # Collect lightweight warnings and print
    warnings = schedule.conflict_warnings()
    print("\nConflict warnings:")
    if warnings:
        for w in warnings:
            print("-", w)
    else:
        print("No conflicts detected.")

    # Verify filtering by status and pet name
    print("\nTasks for pet 'Buddy':")
    buddy_tasks = owner.get_tasks_by_pet_name("Buddy")
    for t in buddy_tasks:
        print(f"- {t.title} [{t.status}]")

    print("\nCompleted tasks (none yet expected):")
    completed = schedule.filter_tasks(status="completed")
    print(completed)

    # Mark one task as completed and verify filtering again
    if sorted_tasks:
        sorted_tasks[0].mark_complete()

    print("\nTasks for pet 'Buddy' marked completed:")
    completed_buddy = owner.get_tasks_by_pet_name("Buddy", status="completed")
    for t in completed_buddy:
        print(f"- {t.title} [{t.status}]")

    print("\nScheduled tasks details:")
    print("{:<18} {:<10} {:>7} {:<8} {:<11}".format("Title", "Type", "Duration", "Priority", "Time"))
    print("-" * 60)
    for task in scheduled_tasks:
        start = task.scheduled_start.strftime("%H:%M") if task.scheduled_start else "--:--"
        end = task.scheduled_end.strftime("%H:%M") if task.scheduled_end else "--:--"
        print(
            "{:<18} {:<10} {:>3}m {:<8} {:<11}".format(
                task.title,
                task.type,
                task.duration_min,
                task.priority.name.lower(),
                f"{start}-{end}",
            )
        )


if __name__ == "__main__":
    main()
