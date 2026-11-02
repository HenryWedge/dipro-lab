from dataclasses import dataclass
from typing import Any


@dataclass(eq=False)
class Event:
    case_id: str
    activity: str
    location: str
    time: Any
    node_id: str | None = None

    def __post_init__(self):
        if self.node_id is None:
            self.node_id = self.location

    def __str__(self):
        return f"[{self.case_id}, {self.activity}, {self.location}, {self.time}]"
