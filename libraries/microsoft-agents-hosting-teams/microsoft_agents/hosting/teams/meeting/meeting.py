from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.core import (
    AgentApplication,
    RouteHandler,
    RouteSelector,
    TurnContext,
    TurnState
)

class Meeting:

    def __init__(self, app: AgentApplication):
        self._app = app

    def _on_meeting_event_selector(self, event_name: str) -> RouteSelector:
        name_to_check = f"application/vnd.microsoft.{event_name}"
        async def route_selector(context: TurnContext) -> bool:
            return context.activity.type == ActivityTypes.event and \
                context.activity.channel_id == MS_TEAMS and \
                context.activity.name == name_to_check
        return route_selector
    
    def _on_meeting_event(self, handler: RouteHandler, event_name: str) -> RouteHandler:
        return self._app.on_route(
            self._on_meeting_event_selector(event_name),
            handler
        )

    def on_meeting_start(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingStart")
    
    def on_meeting_end(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingEnd")
    
    def on_participants_join(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingParticipantJoin") # robrandao: TODO -> discrepancy in names?

    def on_participants_leave(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingParticipantLeave") # robrandao: TODO -> discrepancy in names?
    
    def on_room_join(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingRoomJoin")
    
    def on_room_leave(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingRoomLeave")
    
    def on_stage_view(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingStageView")
    
    def on_smart_reply(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingSmartReply")
    
    def on_reaction(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingReaction")

    def on_poll_response(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingPollResponse")
    
    def on_apps_installed(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingAppsInstalled")
    
    def on_apps_uninstalled(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingAppsUninstalled")
    
    def on_recording_started(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingRecordingStarted")
    
    def on_recording_stopped(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingRecordingStopped")
    
    def on_focus_change(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingFocusChange")

    def on_screen_share_start(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingScreenShareStart")

    def on_screen_share_stop(self, handler: RouteHandler) -> RouteHandler:
        return self._on_meeting_event(handler, "meetingScreenShareStop")
    