from enum import Enum


class ConversationUpdateTypes(str, Enum):
    CHANNEL_CREATED = "channelCreated"
    CHANNEL_RENAMED = "channelRenamed"
    CHANNEL_DELETED = "channelDeleted"
    CHANNEL_RESTORED = "channelRestored"
    MEMBERS_ADDED = "membersAdded"
    MEMBERS_REMOVED = "membersRemoved"
    TEAM_RENAMED = "teamRenamed"
    TEAM_DELETED = "teamDeleted"
    TEAM_ARCHIVED = "teamArchived"
    TEAM_UNARCHIVED = "teamUnarchived"
    TEAM_RESTORED = "teamRestored"
