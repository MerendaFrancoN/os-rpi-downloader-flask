from dataclasses import dataclass
from enum import Enum
from typing import Dict


class JobState(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    FINALIZED = "FINALIZED"


@dataclass
class JobProgressMetadata:
    state: JobState
    total_value: int
    current_value: int

    @property
    def progress(self) -> float:
        return self.current_value * 1.0 / self.total_value

    @property
    def to_json(self) -> Dict:
        return {
            "state": self.state,
            "progress": self.progress
        }

