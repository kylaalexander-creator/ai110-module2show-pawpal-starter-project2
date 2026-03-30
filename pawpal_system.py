from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import uuid


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    id: uuid.UUID
    title: str
    duration_min: int
    priority: Priority
    type: str
    notes: str = ""
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    completed: bool = False

    def validate(self) -> bool:
        """Return True if task data is valid."""
        if self.duration_min <= 0:
            return False
        if not isinstance(self.priority, Priority):
            return False
        if not self.title.strip():
            return False
        if not self.type.strip():
            return False
        return True

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def info(self) -> str:
        """Return a human-readable task summary."""
        if self.completed:
            status = "completed"
        elif self.scheduled_start:
            status = "scheduled"
        else:
            status = "pending"
        return (
            f"Task(id={self.id}, title={self.title}, duration={self.duration_min}m, "
            f"priority={self.priority.name.lower()}, type={self.type}, status={status})"
        )


@dataclass
class Pet:
    id: uuid.UUID
    name: str
    species: str
    age: int
    needs: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def update_needs(self, needs: List[str]) -> None:
        """Replace the pet's need list."""
        self.needs = needs

    def add_task(self, task: Task) -> None:
        """Assign a valid task to the pet."""
        if task.validate():
            self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return tasks assigned to this pet."""
        return self.tasks


@dataclass
class Schedule:
    id: uuid.UUID
    date: date
    total_time_available: int
    owner_id: Optional[uuid.UUID] = None
    pet_id: Optional[uuid.UUID] = None
    tasks: List[Task] = field(default_factory=list)
    scheduled_tasks: List[Task] = field(default_factory=list)

    def add_task(self, t: Task) -> bool:
        """Add a task if valid and within available time."""
        if not t.validate():
            return False
        if t.scheduled_start and t.scheduled_end and self.has_overlap(t):
            return False
        if self.get_planned_duration() + t.duration_min > self.total_time_available:
            return False
        self.tasks.append(t)
        return True

    def remove_task(self, task_id: uuid.UUID) -> bool:
        """Remove a task from the schedule by ID."""
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                break
        else:
            return False

        # also remove if already scheduled
        self.scheduled_tasks = [t for t in self.scheduled_tasks if t.id != task_id]
        return True

    def has_overlap(self, new_task: Task, in_tasks: Optional[List[Task]] = None) -> bool:
        """Check whether a task overlaps with existing scheduled tasks."""
        if new_task.scheduled_start is None or new_task.scheduled_end is None:
            return False
        container = in_tasks if in_tasks is not None else self.scheduled_tasks
        for t in container:
            if t.scheduled_start and t.scheduled_end:
                if (
                    new_task.scheduled_start < t.scheduled_end
                    and t.scheduled_start < new_task.scheduled_end
                ):
                    return True
        return False

    def get_planned_duration(self) -> int:
        """Return the total duration of planned tasks."""
        return sum(task.duration_min for task in self.tasks)

    def generate_plan(self) -> List[Task]:
        """Schedule tasks in priority order up to available time."""
        sorted_tasks = sorted(
            self.tasks,
            key=lambda x: (-x.priority.value, x.duration_min),
        )

        scheduled_tasks: List[Task] = []
        current_time = datetime.combine(self.date, datetime.min.time())
        used_minutes = 0

        for task in sorted_tasks:
            if used_minutes + task.duration_min > self.total_time_available:
                continue
            candidate_start = current_time
            candidate_end = current_time + timedelta(minutes=task.duration_min)
            task.scheduled_start = candidate_start
            task.scheduled_end = candidate_end

            if self.has_overlap(task, in_tasks=scheduled_tasks):
                continue

            scheduled_tasks.append(task)
            used_minutes += task.duration_min
            current_time = candidate_end

        self.scheduled_tasks = scheduled_tasks
        return scheduled_tasks

    def explain(self) -> str:
        """Return a human-readable description of the schedule."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."

        lines = [f"Schedule {self.id} on {self.date} (available {self.total_time_available}m):"]
        for t in self.scheduled_tasks:
            start = t.scheduled_start.strftime("%H:%M") if t.scheduled_start else "?"
            end = t.scheduled_end.strftime("%H:%M") if t.scheduled_end else "?"
            lines.append(
                f"- {t.title} [{t.type}] {t.duration_min}m, p={t.priority.name.lower()}: {start}-{end}"
            )

        lines.append(f"Total planned duration {self.get_planned_duration()}m")
        return "\n".join(lines)


@dataclass
class Owner:
    id: uuid.UUID
    name: str
    email: str
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)
    schedule: Optional[Schedule] = None

    def add_pet(self, p: Pet) -> None:
        """Add a pet to the owner's list if it isn't already present."""
        if not any(existing.id == p.id for existing in self.pets):
            self.pets.append(p)

    def remove_pet(self, pet_id: uuid.UUID) -> bool:
        """Remove a pet by its ID, returning whether removal succeeded."""
        for i, p in enumerate(self.pets):
            if p.id == pet_id:
                del self.pets[i]
                return True
        return False

    def get_pets(self) -> List[Pet]:
        """Return the owner's pet list."""
        return self.pets

    def set_schedule(self, s: Schedule) -> None:
        """Set the owner's schedule."""
        self.schedule = s

    def get_schedule(self) -> Optional[Schedule]:
        """Get the owner's schedule, if any."""
        return self.schedule


def demo_usage() -> None:
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet = Pet(id=uuid.uuid4(), name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    schedule = Schedule(
        id=uuid.uuid4(),
        date=date.today(),
        total_time_available=240,
        owner_id=owner.id,
        pet_id=pet.id,
    )

    schedule.add_task(Task(id=uuid.uuid4(), title="Morning walk", duration_min=30, priority=Priority.HIGH, type="walk"))
    schedule.add_task(Task(id=uuid.uuid4(), title="Feed pet", duration_min=15, priority=Priority.MEDIUM, type="feeding"))
    schedule.add_task(Task(id=uuid.uuid4(), title="Play time", duration_min=20, priority=Priority.LOW, type="enrichment"))

    schedule.generate_plan()
    owner.set_schedule(schedule)

    print(owner.get_schedule().explain())


if __name__ == "__main__":
    demo_usage()
