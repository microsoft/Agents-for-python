from enum import Enum

class BotType(str, Enum):
    published = "published"
    prebuilt = "prebuilt"
