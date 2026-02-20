from enum import Enum, auto

class StorageOperation(Enum):
    read = auto()
    write = auto()
    delete = auto()