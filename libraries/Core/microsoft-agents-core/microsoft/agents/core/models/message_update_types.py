from enum import Enum


class MessageUpdateTypes(str, Enum):
    EDIT_MESSAGE = "editMessage"
    SOFT_DELETE_MESSAGE = "softDeleteMessage"
    UNDELETE_MESSAGE = "undeleteMessage"
