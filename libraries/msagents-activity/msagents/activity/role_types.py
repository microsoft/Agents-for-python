from enum import Enum


class RoleTypes(str, Enum):
    user = "user"
    agent = "bot"
    skill = "skill"
