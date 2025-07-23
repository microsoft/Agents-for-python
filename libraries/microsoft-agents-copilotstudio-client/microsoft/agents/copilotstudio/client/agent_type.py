from enum import Enum


class AgentType(str, Enum):
    PUBLISHED = "published"
    PREBUILT = "prebuilt"
