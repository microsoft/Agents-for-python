from enum import Enum


class ActivityEventNames(str, Enum):
    continue_conversation = "ContinueConversation"
    create_conversation = "CreateConversation"
