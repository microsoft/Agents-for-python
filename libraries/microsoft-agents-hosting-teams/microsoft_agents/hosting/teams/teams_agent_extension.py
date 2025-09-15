from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentExtension,
    RouteHandler,
    RouteSelector,
    TurnContext,
    TurnState
)

from .meeting.meeting import Meeting
from .activity_extensions import TeamsChannelDataParser
from .message_extension import MessageExtension
from .task_module import TaskModule
from .feedback_loop_data import FeedbackLoopData

MS_TEAMS = "msteams"

# robrandao: TODO -> addroute

class TeamsAgentExtension(AgentExtension):
    
    def __init__(self):
        super().__init__(MS_TEAMS)
        self._app = None
        self._meeting = None
        self._message_extension = None
        self._task_module = None
        # robrandao: TODO

    @property
    def meeting(self) -> Meeting:
        return self._meeting
    
    @property
    def message_extension(self) -> MessageExtension:
        return self._message_extension
    
    @property
    def task_module(self) -> TaskModule:
        return self._task_module
    
    def on_feedback(self, handler: RouteHandler):
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.invoke and
                context.activity.channel_id == MS_TEAMS and
                context.activity.name == "message/submitAction" and
                context.activity.value.action_name == "feedback"
            
        self.add_route(route_selector, handler):
        return self
    
    def _on_message_event(self, handler: RouteHandler, activity_type: str, event_type: str):
        async def route_selector(context: TurnContext) -> bool:
            channel_data = parse_teams_channel_data(context.activity.channel_data)
            return context.activity.type == activity_type and
                channel_data and
                channel_data.event_type == event_type
        self.add_route(route_selector, handler, False)
        return self

    def on_message_edit(self, handler: RouteHandler):
        return self._on_message_event(handler, ActivityTypes.message_update, "editMessage")
    
    def on_message_delete(self, handler: RouteHandler):
        return self._on_message_event(handler, ActivityTypes.message_delete, "softDeleteMessage")
    
    def on_message_undelete(self, handler: RouteHandler):
        return self._on_message_event(handler, ActivityTypes.message_update, "undeleteMessage")
    
    def on_teams_members_added(self, handler: RouteHandler):
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.conversation_update and
                context.activity.channel_id == MS_TEAMS and
                context.activity.members_added and
                len(context.activity.members_added) > 0
        self.add_route(route_selector, handler, False)
        return self
    
    def on_teams_members_removed(self, handler: RouteHandler):
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.conversation_update and
                context.activity.channel_id == MS_TEAMS and
                context.activity.members_removed and
                len(context.activity.members_removed) > 0
        self.add_route(route_selector, handler, False)
        return self

    def _on_teams_conversation_event(self, handler: RouteHandler, event_type: str):
        async def route_selector(context: TurnContext) -> bool:
            channel_data = parse_teams_channel_data(context.activity.channel_data)
            return context.activity.type == ActivityTypes.conversation_update and
                context.activity.channel_id == MS_TEAMS and
                channel_data and
                channel_data.event_type == event_type
        self.add_route(route_selector, handler, False)
        return self
    
    def on_teams_channel_created(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelCreated")
    
    def on_teams_channel_deleted(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelDeleted")

    def on_teams_channel_renamed(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelRenamed")
    
    def on_teams_channel_restored(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelRestored")

    def on_teams_channel_shared(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelShared")
    
    def on_teams_channel_unshared(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "channelUnshared")

    def on_teams_team_renamed(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamRenamed")
    
    def on_teams_team_archived(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamArchived")
    
    def on_teams_team_unarchived(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamUnarchived")
    
    def on_teams_team_deleted(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamDeleted")
    
    def on_teams_team_hard_deleted(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamHardDeleted")
    
    def on_teams_team_restored(self, handler: RouteHandler):
        return self._on_teams_conversation_event(handler, "teamRestored")