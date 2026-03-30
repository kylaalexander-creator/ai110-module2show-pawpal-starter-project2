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

    # Add at least three tasks (different durations and priorities)
    schedule.add_task(Task(
        id=uuid.uuid4(),
        title="Morning walk",
        duration_min=30,
        priority=Priority.HIGH,
        type="walk",
        notes="Walk Buddy around the park",
    ))

    schedule.add_task(Task(
        id=uuid.uuid4(),
        title="Feed Whiskers",
        duration_min=15,
        priority=Priority.MEDIUM,
        type="feeding",
        notes="Wet food and water",
    ))

    schedule.add_task(Task(
        id=uuid.uuid4(),
        title="Play session",
        duration_min=45,
        priority=Priority.LOW,
        type="play",
        notes="Interactive toys for both pets",
    ))

    schedule.add_task(Task(
        id=uuid.uuid4(),
        title="Vet medication",
        duration_min=10,
        priority=Priority.HIGH,
        type="care",
        notes="Give daily meds to Buddy",
    ))

    # Generate plan and attach to owner
    scheduled_tasks = schedule.generate_plan()
    owner.set_schedule(schedule)

    # Print today's schedule
    print("Today's Schedule")
    print("===============")
    print(owner.get_schedule().explain())

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
