from enum import Enum


class ContactRelationUpdateActionTypes(str, Enum):
    add = "add"
    remove = "remove"
