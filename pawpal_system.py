from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
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
    created_date: date = field(default_factory=date.today)
    recurrence_days: Optional[int] = None
    last_completed_date: Optional[date] = None

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
        if self.recurrence_days is not None and self.recurrence_days <= 0:
            return False
        return True

    @property
    def status(self) -> str:
        if self.completed:
            return "completed"
        if self.scheduled_start is not None:
            return "scheduled"
        return "pending"

    def is_recurring(self) -> bool:
        """Return True if the task is configured to repeat periodically."""
        return self.recurrence_days is not None and self.recurrence_days > 0

    def should_run_on(self, target_date: date) -> bool:
        """Return True when the task occurrence should be scheduled for the target date."""
        if not self.is_recurring():
            return False
        delta = target_date - self.created_date
        return delta.days >= 0 and delta.days % self.recurrence_days == 0

    def next_occurrence(self, after_date: Optional[date] = None) -> Optional[date]:
        """Compute the next recurrence date after the given date (or today)."""
        if not self.is_recurring():
            return None
        if after_date is None:
            after_date = date.today()
        delta_days = (after_date - self.created_date).days
        if delta_days < 0:
            return self.created_date
        cycles = delta_days // self.recurrence_days
        next_date = self.created_date + timedelta(days=(cycles + 1) * self.recurrence_days)
        return next_date

    def copy_for_date(self, target_date: date) -> Task:
        return Task(
            id=uuid.uuid4(),
            title=self.title,
            duration_min=self.duration_min,
            priority=self.priority,
            type=self.type,
            notes=self.notes,
            created_date=self.created_date,
            recurrence_days=self.recurrence_days,
            last_completed_date=self.last_completed_date,
        )

    def mark_complete(self) -> Optional[Task]:
        """Mark the task done and, if recurring, create and return next occurrence task.

        Behavior:
        - marks current task as completed
        - records last completion date
        - if recurrence_days is set, returns a new Task for the next recurrence
        - otherwise returns None
        """
        self.completed = True
        self.last_completed_date = date.today()

        if not self.is_recurring():
            return None

        next_date = self.next_occurrence(self.last_completed_date)
        if next_date is None:
            return None

        new_task = Task(
            id=uuid.uuid4(),
            title=self.title,
            duration_min=self.duration_min,
            priority=self.priority,
            type=self.type,
            notes=self.notes,
            created_date=next_date,
            recurrence_days=self.recurrence_days,
        )
        return new_task

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

    def get_tasks_by_status(self, status: str) -> List[Task]:
        status = status.lower().strip()
        if status not in {"pending", "scheduled", "completed"}:
            return []
        return [task for task in self.tasks if task.status == status]

    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        task_type = task_type.lower().strip()
        return [task for task in self.tasks if task.type.lower() == task_type]


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

    def sort_tasks_by_time(self) -> List[Task]:
        """Return tasks ordered by scheduled start time."""
        return sorted(
            [t for t in self.tasks if t.scheduled_start is not None],
            key=lambda x: x.scheduled_start,
        )

    def filter_tasks(self, status: Optional[str] = None, task_type: Optional[str] = None) -> List[Task]:
        """Return tasks matching optional status and type filters."""
        targets = self.tasks
        if status:
            status = status.lower().strip()
            targets = [t for t in targets if t.status == status]
        if task_type:
            task_type = task_type.lower().strip()
            targets = [t for t in targets if t.type.lower() == task_type]
        return targets

    def detect_conflicts(self) -> List[Tuple[Task, Task]]:
        """Return overlapping task pairs (same Schedule)."""
        conflicts = []
        scheduled = [t for t in self.tasks if t.scheduled_start and t.scheduled_end]
        scheduled = sorted(scheduled, key=lambda t: t.scheduled_start)

        for i in range(len(scheduled)):
            for j in range(i + 1, len(scheduled)):
                t1 = scheduled[i]
                t2 = scheduled[j]
                if t1.scheduled_end and t2.scheduled_start and t1.scheduled_end > t2.scheduled_start:
                    conflicts.append((t1, t2))
        return conflicts

    def conflict_warnings(self) -> List[str]:
        """Return non-exception warning strings for conflicts (lightweight alert mechanism)."""
        conflicts = self.detect_conflicts()
        warnings = []
        for t1, t2 in conflicts:
            warnings.append(
                f"Warning: task '{t1.title}' ({t1.scheduled_start.strftime('%H:%M')}-{t1.scheduled_end.strftime('%H:%M')}) "
                f"overlaps with '{t2.title}' ({t2.scheduled_start.strftime('%H:%M')}-{t2.scheduled_end.strftime('%H:%M')})."
            )
        return warnings


    def tasks_due_today(self) -> List[Task]:
        """Return tasks that are scheduled for the current schedule date, including recurring tasks."""
        due = []
        for t in self.tasks:
            if t.is_recurring() and t.should_run_on(self.date):
                due.append(t.copy_for_date(self.date))
            elif not t.is_recurring():
                due.append(t)
        return due

    def complete_task(self, task_id: uuid.UUID) -> Optional[Task]:
        """Mark a task complete; if recurring, create and add next occurrence."""
        target: Optional[Task] = None
        for t in self.tasks:
            if t.id == task_id:
                target = t
                break

        if target is None:
            return None

        new_task = target.mark_complete()

        if new_task is not None:
            added = self.add_task(new_task)
            if not added:
                # if we can't add due to time constraints, incorporate as pending only
                self.tasks.append(new_task)

        return new_task

    def generate_plan(self) -> List[Task]:
        """Schedule tasks in priority order up to available time."""
        tasks_for_today = self.tasks_due_today()
        sorted_tasks = sorted(
            tasks_for_today,
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

    def get_tasks(self, pet_id: Optional[uuid.UUID] = None, status: Optional[str] = None) -> List[Task]:
        """Return tasks across pets, with optional pet and status filters."""
        tasks: List[Task] = []
        for p in self.pets:
            if pet_id and p.id != pet_id:
                continue
            tasks.extend(p.tasks)

        if status:
            status = status.lower().strip()
            tasks = [t for t in tasks if t.status == status]

        return tasks

    def get_tasks_by_pet_name(self, pet_name: str, status: Optional[str] = None) -> List[Task]:
        """Return tasks for a named pet, optionally filtered by completion status."""
        pet_name_lower = pet_name.strip().lower()
        tasks: List[Task] = []
        for p in self.pets:
            if p.name.strip().lower() == pet_name_lower:
                tasks.extend(p.tasks)

        if status:
            status = status.lower().strip()
            tasks = [t for t in tasks if t.status == status]

        return tasks

    def set_schedule(self, s: Schedule) -> None:
        """Set the owner's schedule."""
        self.schedule = s

    def get_schedule(self) -> Optional[Schedule]:
        """Get the owner's schedule, if any."""
        return self.schedule

    def detect_conflicts(self) -> List[Tuple[Task, Task, uuid.UUID, uuid.UUID]]:
        """Detect overlapping tasks across all pets. Returns each conflict pair plus involved pet IDs."""
        all_scheduled = []
        for pet in self.pets:
            for task in pet.tasks:
                if task.scheduled_start and task.scheduled_end:
                    all_scheduled.append((pet.id, task))

        sorted_scheduled = sorted(all_scheduled, key=lambda x: x[1].scheduled_start)

        conflicts: List[Tuple[Task, Task, uuid.UUID, uuid.UUID]] = []
        for i in range(len(sorted_scheduled)):
            pet_i, task_i = sorted_scheduled[i]
            for j in range(i + 1, len(sorted_scheduled)):
                pet_j, task_j = sorted_scheduled[j]
                if task_i.scheduled_end and task_j.scheduled_start and task_i.scheduled_end > task_j.scheduled_start:
                    # Overlap found
                    conflicts.append((task_i, task_j, pet_i, pet_j))
                elif task_j.scheduled_start and task_i.scheduled_end and task_i.scheduled_end <= task_j.scheduled_start:
                    # Because sorted by start time, we can break once no overlap with current i
                    break
        return conflicts

    def conflict_warnings(self) -> List[str]:
        """Return lightweight warnings across all pets for overlapping tasks."""
        conflicts = self.detect_conflicts()
        warnings = []
        for t1, t2, p1, p2 in conflicts:
            warnings.append(
                f"Warning: pet {p1} task '{t1.title}' ({t1.scheduled_start.strftime('%H:%M')}-{t1.scheduled_end.strftime('%H:%M')}) "
                f"overlaps with pet {p2} task '{t2.title}' ({t2.scheduled_start.strftime('%H:%M')}-{t2.scheduled_end.strftime('%H:%M')})."
            )
        return warnings


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
