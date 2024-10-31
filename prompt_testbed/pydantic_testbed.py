from pydantic import BaseModel
from typing import TypedDict
from enum import Enum
import json


class StatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(TypedDict):
    id: int
    name: str
    status: StatusEnum


class Task2(BaseModel):
    id: int
    name: str
    status: StatusEnum


# Example usage
task = Task(id=1, name="Sample Task", status=StatusEnum.PENDING)
print(task["status"])
print(task["status"] == StatusEnum.PENDING)
print(task["status"] == StatusEnum.IN_PROGRESS)

# Output
task_json = json.dumps(task)
print(task_json)

task2 = Task2(id=2, name="Sample Task", status=StatusEnum.PENDING)
print(task2.status)
print(task2.status == StatusEnum.PENDING)
print(task2.status == StatusEnum.IN_PROGRESS)

# Output
task2_json = task2.model_dump_json()
print(task2_json)
