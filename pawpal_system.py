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
    priority: int
    type: str
    notes: str = ""
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    def validate(self) -> bool:
        if self.duration_min <= 0:
            return False
        if self.priority not in (1, 2, 3):
            return False
        if not self.title.strip():
            return False
        if not self.type.strip():
            return False
        return True

    def info(self) -> str:
        status = "scheduled" if self.scheduled_start else "pending"
        return (
            f"Task(id={self.id}, title={self.title}, duration={self.duration_min}m, "
            f"priority={self.priority}, type={self.type}, status={status})"
        )


@dataclass
class Pet:
    id: uuid.UUID
    name: str
    species: str
    age: int
    needs: List[str] = field(default_factory=list)

    def update_needs(self, needs: List[str]) -> None:
        self.needs = needs


@dataclass
class Schedule:
    id: uuid.UUID
    date: date
    total_time_available: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, t: Task) -> bool:
        if not t.validate():
            return False
        if self.has_overlap(t):
            return False
        if self.get_planned_duration() + t.duration_min > self.total_time_available:
            return False
        self.tasks.append(t)
        return True

    def remove_task(self, task_id: uuid.UUID) -> bool:
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def has_overlap(self, new_task: Task) -> bool:
        if new_task.scheduled_start is None or new_task.scheduled_end is None:
            return False
        for t in self.tasks:
            if t.scheduled_start and t.scheduled_end:
                if (
                    new_task.scheduled_start < t.scheduled_end
                    and t.scheduled_start < new_task.scheduled_end
                ):
                    return True
        return False

    def get_planned_duration(self) -> int:
        return sum(task.duration_min for task in self.tasks)

    def generate_plan(self) -> List[Task]:
        # simple greedy plan by priority and shortest duration
        sorted_tasks = sorted(
            self.tasks,
            key=lambda x: (-x.priority, x.duration_min),
        )

        scheduled_tasks: List[Task] = []
        current_time = datetime.combine(self.date, datetime.min.time())
        used_minutes = 0

        for task in sorted_tasks:
            if used_minutes + task.duration_min > self.total_time_available:
                continue
            task.scheduled_start = current_time
            task.scheduled_end = current_time + timedelta(minutes=task.duration_min)
            if any(
                (task.scheduled_start < existing.scheduled_end)
                and (existing.scheduled_start < task.scheduled_end)
                for existing in scheduled_tasks
            ):
                continue
            scheduled_tasks.append(task)
            current_time = task.scheduled_end
            used_minutes += task.duration_min

        self.tasks = scheduled_tasks
        return scheduled_tasks

    def explain(self) -> str:
        if not self.tasks:
            return "No tasks scheduled."

        lines = [f"Schedule {self.id} on {self.date} (available {self.total_time_available}m):"]
        for t in self.tasks:
            start = t.scheduled_start.strftime("%H:%M") if t.scheduled_start else "?"
            end = t.scheduled_end.strftime("%H:%M") if t.scheduled_end else "?"
            lines.append(f"- {t.title} [{t.type}] {t.duration_min}m, p={t.priority}: {start}-{end}")

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
        self.pets.append(p)

    def remove_pet(self, pet_id: uuid.UUID) -> bool:
        for i, p in enumerate(self.pets):
            if p.id == pet_id:
                del self.pets[i]
                return True
        return False

    def get_pets(self) -> List[Pet]:
        return self.pets

    def set_schedule(self, s: Schedule) -> None:
        self.schedule = s

    def get_schedule(self) -> Optional[Schedule]:
        return self.schedule


def demo_usage() -> None:
    owner = Owner(id=uuid.uuid4(), name="Jordan", email="jordan@example.com")
    pet = Pet(id=uuid.uuid4(), name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    schedule = Schedule(id=uuid.uuid4(), date=date.today(), total_time_available=240)
    schedule.add_task(Task(id=uuid.uuid4(), title="Morning walk", duration_min=30, priority=3, type="walk"))
    schedule.add_task(Task(id=uuid.uuid4(), title="Feed pet", duration_min=15, priority=2, type="feeding"))
    schedule.add_task(Task(id=uuid.uuid4(), title="Play time", duration_min=20, priority=1, type="enrichment"))

    schedule.generate_plan()
    owner.set_schedule(schedule)

    print(owner.get_schedule().explain())


if __name__ == "__main__":
    demo_usage()
