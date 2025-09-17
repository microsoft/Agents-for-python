from ast import Str
from strenum import StrEnum

from microsoft_agents.hosting.core import ConversationUpdateEvents

class ChannelTypes(StrEnum):
    PRIVATE = "private"
    SHARED = "shared"
    STANDARD = "standard"

class TeamsConversationUpdateEvents(StrEnum, ConversationUpdateEvents):
    CHANNEL_CREATED = "channelCreated"
    CHANNEL_RENAMED = "channelRenamed"
    CHANNEL_DELETED = "channelDeleted"
    CHANNEL_RESTORED = "channelRestored"
    
    TEAM_RENAMED = "teamRenamed"
    TEAM_DELETED = "teamDeleted"
    TEAM_HARD_DELETED = "teamHardDeleted"
    TEAM_ARCHIVED = "teamArchived"
    TEAM_UNARCHIVED = "teamUnarchived"
    TEAM_RESTORED = "teamRestored"

    TOPIC_NAME = "topicName"
    HISTORY_DISCLOSED = "historyDisclosed"

class TeamsMessageEvents(StrEnum):
    UNDELETE_MESSAGE = "undeleteMessage"
    SOFT_DELETE_MESSAGE = "softDeleteMessage"
    EDIT_MESSAGE = "editMessage"