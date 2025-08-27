from enum import Enum


class ActivityImportance(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
