from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
from typing import List, Optional, Tuple


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    DONE = "done"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    notes: str = ""
    status: TaskStatus = TaskStatus.PENDING
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    def __post_init__(self):
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be positive")

    def set_schedule(self, start: datetime):
        self.scheduled_start = start
        self.scheduled_end = start + timedelta(minutes=self.duration_minutes)
        self.status = TaskStatus.SCHEDULED


@dataclass
class Pet:
    name: str
    species: str
    age_years: Optional[float] = None
    weight_kg: Optional[float] = None
    needs: List[str] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    availability_start: time = time(hour=8, minute=0)
    availability_end: time = time(hour=20, minute=0)
    preferences: List[str] = field(default_factory=list)


@dataclass
class Schedule:
    pet: Pet
    owner: Owner
    date: datetime
    tasks: List[Task] = field(default_factory=list)
    scheduled_tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def _availability_window(self) -> Tuple[datetime, datetime]:
        start = datetime.combine(self.date.date(), self.owner.availability_start)
        end = datetime.combine(self.date.date(), self.owner.availability_end)
        if end <= start:
            raise ValueError("Owner availability end must be after start")
        return start, end

    def generate_plan(self):
        self.scheduled_tasks.clear()
        window_start, window_end = self._availability_window()
        current_time = window_start

        # sort by priority high->low, then short duration first for fit in schedule
        by_priority = sorted(
            self.tasks,
            key=lambda t: (t.priority.value, t.duration_minutes),
            reverse=True,
        )

        for task in by_priority:
            if current_time + timedelta(minutes=task.duration_minutes) <= window_end:
                task.set_schedule(current_time)
                self.scheduled_tasks.append(task)
                current_time = task.scheduled_end

        return self.scheduled_tasks

    def explain_plan(self) -> str:
        if not self.scheduled_tasks:
            return "No tasks were scheduled. Either there are no tasks or time is insufficient."

        lines = [f"Schedule for {self.date.date()} ({self.pet.name})"]
        for task in self.scheduled_tasks:
            start = task.scheduled_start.strftime("%H:%M") if task.scheduled_start else "?"
            end = task.scheduled_end.strftime("%H:%M") if task.scheduled_end else "?"
            lines.append(
                f"- {task.title} ({task.duration_minutes}m, {task.priority.value}) -> {start} to {end}"
            )
        return "\n".join(lines)


def demo_usage() -> None:
    pet = Pet(name="Mochi", species="dog", age_years=3)
    owner = Owner(name="Jordan")
    schedule = Schedule(pet=pet, owner=owner, date=datetime.now())

    schedule.add_task(Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH))
    schedule.add_task(Task(title="Feed pet", duration_minutes=15, priority=Priority.MEDIUM))
    schedule.add_task(Task(title="Play time", duration_minutes=20, priority=Priority.LOW))

    schedule.generate_plan()
    print(schedule.explain_plan())


if __name__ == "__main__":
    demo_usage()
