from enum import Enum


class InstallationUpdateActionTypes(str, Enum):
    add = "add"
    remove = "remove"
