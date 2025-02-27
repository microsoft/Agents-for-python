from enum import Enum


class BotType(str, Enum):
    PUBLISHED = "published"
    PREBUILT = "prebuilt"
