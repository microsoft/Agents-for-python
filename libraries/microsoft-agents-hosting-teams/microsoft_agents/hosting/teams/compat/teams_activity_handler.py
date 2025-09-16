from pydoc import resolve
from typing import Any, Awaitable

from microsoft_agents.hosting.core import (
    ActivityHandler,
    InvokeResponse,
    TurnContext
)
from openai import BadRequestError
from pytest import param

from ..messages_extension import (
    AppBasedLinkQuery,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    parseValueMessagingExtensionQuery
)

from ..file import FileConsentCardResponse
from ..activity_extensions import (
    ChannelInfo,
    parseTeamsChannelData,
    TeamInfo,
    TeamsChannelAccount
)
from ..meeting import (
    MeetingEndEventDetails,
    MeetingParticipantsEventDetails,
    MeetingStartEventDetails,
    TeamsMeetingMember
)
from .read_receipt_info import ReadReceiptInfo

async def create_callback(
    handler: Awaitable[[TurnContext, Awaitable[None, None]]]
) -> Awaitable[[TurnContext, Awaitable[None, None]], None]:
    async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
        await handler(context, next)
    return callback

async def create_callback_with_team_info(
    handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
) -> Awaitable[[TurnContext, Awaitable[None, None]], None]:
    async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
        teams_channel_data = parseTeamsChannelData(context.activity.channel_data)
        await handler(TeamInfo(teams_channel_data.team), context, next)
    return callback

async def create_callback_with_channel_info(
    handler: Awaitable[[ChannelInfo, TeamInfo, TurnContext, Awaitable[None, None]]]
) -> Awaitable[[TurnContext, Awaitable[None, None]], None]:
    async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
        teams_channel_data = parseTeamsChannelData(context.activity.channel_data)
        await handler(ChannelInfo(teams_channel_data.channel), TeamInfo(teams_channel_data.team), context, next)
    return callback

class TeamsActivityHandler(ActivityHandler):

    async def _on_invoke_activity(context: TurnContext) -> InvokeResponse:
        run_events = True

        try:
            if not context.activity.name and context.activity.channel_id == MS_TEAMS:
                return await self.handle_teams_card_action_invoke(context)
            else:
                handler_map = {
                    "config/fetch":
                        lambda ctx: self.handle_teams_config_fetch(context, context.activity.value),
                    "config/submit":
                        lambda ctx: self.handle_teams_config_submit(context, context.activity.value),
                    "fileConsent/invoke":
                        lambda ctx: self.handle_teams_file_consent(context, FileConsentCardResponse(context.activity.value)),
                    "actionableMessage/executeAction":
                        None, # Not implemented
                    "composeExtension/queryLink":
                        lambda ctx: self.handle_teams_app_based_link_query(context, AppBasedLinkQuery(context.activity.value)),
                    "composeExtension/anonymousQueryLink":
                        lambda ctx: self.handle_teams_anonymous_app_based_link_query(context, AppBasedLinkQuery(context.activity.value)),
                    "composeExtension/query":
                        lambda ctx: self.handle_teams_messaging_extension_query(context, parseValueMessagingExtensionQuery(context.activity.value)),
                    "composeExtension/selectItem":
                        lambda ctx: self.handle_teams_messaging_extension_select_item(context, context.activity.value),
                    "composeExtension/submitAction":
                        lambda ctx: self.handle_teams_messaging_extension_submit_action_dispatch(context, MessagingExtensionAction(context.activity.value)),
                    "composeExtension/fetchTask":
                        lambda ctx: self.handle_teams_messaging_extension_fetch_task(context, MessagingExtensionAction(context.activity.value)),
                    "composeExtension/querySettingUrl":
                        lambda ctx: self.handle_teams_messaging_extension_configuration_query_setting_url(context, MessagingExtensionQuery(context.activity.value)),
                    "composeExtension/setting": # robrandao: TODO -> JS is different
                        lambda ctx: self.handle_teams_messaging_extension_configuration_setting(context, context.activity.value),
                    "composeExtension/onCardButtonClicked":
                        lambda ctx: self.handle_teams_messaging_extension_card_button_clicked(context, context.activity.value),
                    "task/fetch":
                        lambda ctx: self.handle_teams_task_module_fetch(context, TaskModuleRequest(context.activity.value)),
                    "task/submit":
                        lambda ctx: self.handle_teams_task_module_submit(context, TaskModuleRequest(context.activity.value)),
                    "tab/fetch":
                        None, # Not implemented
                    "tab/submit":
                        None,
                }

                resolved_handler = handler_map.get(context.activity.name)
                if resolved_handler is None:
                    return await super.on_invoke_activity(context)                

                self.create_invoke_response(await resolved_handler(context)) # robrandao: TODO
        except NotImplementedError:
            return InvokeResponse(status=501)
        except BadRequestError:
            return InvokeResponse(status=400)
        finally:
            if run_events:
                await self.default_next_event(context)() # robrandao: TODO

    async def _handle_teams_card_action_invoke(context: TurnContext) -> InvokeResponse:
        raise NotImplementedError()

    async def _handle_teams_config_fetch(context: TurnContext, config_data: Any) -> Any:
        raise NotImplementedError()
    
    async def _handle_teams_config_submit(context: TurnContext, config_data: Any) -> Any:
        raise NotImplementedError()
    
    async def _handle_teams_file_consent(context: TurnContext, file_consent_response: FileConsentCardResponse) -> None:
        if file_consent_response.action == "accept":
            return await self._handle_teams_file_consent_accept(context, file_consent_response)
        elif file_consent_response.action == "decline":
            return await self._handle_teams_file_consent_decline(context, file_consent_response)
        else:
            raise ValueError("Invalid file consent action")
        
    async def _handle_teams_file_consent_accept(context: TurnContext, file_consent_response: FileConsentCardResponse) -> None:
        raise NotImplementedError()
    
    async def _handle_teams_file_consent_decline(context: TurnContext, file_consent_response: FileConsentCardResponse) -> None:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_card_button_clicked(context: TurnContext, card_data: Any) -> None:
        raise NotImplementedError()
    
    async def _handle_teams_task_module_fetch(context: TurnContext, task_module_request: TaskModuleRequest) -> Any:
        raise NotImplementedError()
    
    async def _handle_teams_task_module_submit(context: TurnContext, task_module_request: TaskModuleRequest) -> Any:
        raise NotImplementedError()
    
    async def _handle_teams_app_based_link_query(context: TurnContext, query: AppBasedLinkQuery) -> MessagingExtensionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_anonymous_app_based_link_query(context: TurnContext, query: AppBasedLinkQuery) -> MessagingExtensionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_query(context: TurnContext, query: MessagingExtensionQuery) -> MessagingExtensionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaing_extension_select_item(context: TurnContext, query: Any) -> MessagingExtensionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_submit_action_dispatch(
            context: TurnContext,
            action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        if action.message_preview_action:
            if action.message_preview_action == "edit":
                return await self._handle_teams_messaging_extension_message_preview_edit(context, action)
            elif action.message_preview_action == "send":
                return await self._handle_teams_messaging_extension_message_preview_send(context, action)
            else:
                raise BadRequestError("Invalid message preview action")
        else:
            return await self._handle_teams_messaging_extension_submit_action(context, action)
        
    async def _handle_teams_messaging_extension_submit_action(
            context: TurnContext,
            action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_message_preview_edit(
            context: TurnContext,
            action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_message_preview_send(
            context: TurnContext,
            action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_fetch_task(
            context: TurnContext,
            action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_configuration_query_setting_url(
            context: TurnContext,
            query: MessagingExtensionQuery
    ) -> MessagingExtensionResponse:
        raise NotImplementedError()
    
    async def _handle_teams_messaging_extension_configuration_setting(
            context: TurnContext,
            settings_data: Any
    ) -> None:
        raise NotImplementedError()
    
    async def _dispatch_conversation_update_activity(context: TurnContext) -> None:
        if context.activity.channel_id == MS_TEAMS:
            channel_data = parseTeamsChannelData(context.activity.channel_data)

            if context.activity.members_added and len(context.activity.members_added) > 0:
                return await self._on_teams_members_added(context)
            if context.activity.members_removed and len(context.activity.members_removed) > 0:
                return await self._on_teams_members_removed(context)
            
            if not channel_data or not channel_data.event_type:
                return await super()._dispatch_conversation_update_activity(context)
            
            handler_map = {
                "channelCreated": on_teams_channel_created,
                "channelDeleted": on_teams_channel_deleted,
                "channelRenamed": on_teams_channel_renamed,
                "teamArchived": on_teams_team_archived,
                "teamDeleted": on_teams_team_deleted,
                "teamHardDeleted": on_teams_team_hard_deleted,
                "channelRestored": on_teams_channel_restored,
                "teamRenamed": on_teams_team_renamed,
                "teamRestored": on_teams_team_restored,
                "teamUnarchived": on_teams_team_unarchived,
            }

            resolved_handler = handler_map.get(channel_data.event_type)

            if not resolved_handler:
                return await super()._dispatch_conversation_update_activity(context)
            
            return await resolved_handler(context)
        
    async def _dispatch_message_update_activity(context: TurnContext) -> None:
        if context.activity.channel_id == MS_TEAMS:
            channel_data = parseTeamsChannelData(context.activity.channel_data)

            if channel_data.event_type == "undeleteMessage":
                return await self._on_teams_undelete_message(context)
            elif channel_data.event_type == "editMessage":
                return await self._on_teams_edit_message(context)
        return await super()._dispatch_message_update_activity(context)

    async def _dispatch_message_delete_activity(context: TurnContext) -> None:
        if context.activity.channel_id == MS_TEAMS:
            channel_data = parseTeamsChannelData(context.activity.channel_data)

            if channel_data.event_type == "softDeleteMessage":
                return await self._on_teams_soft_delete_message(context)
        return await super()._dispatch_message_delete_activity(context)
    
    async def _on_teams_message_undelete(context: TurnContext) -> None:
        await self.handle(context, "TeamsMessageUndelete", self.default_next_event(context))

    async def _on_teams_message_edit(context: TurnContext) -> None:
        await self.handle(context, "TeamsMessageEdit", self.default_next_event(context))

    async def _on_teams_message_soft_delete(context: TurnContext) -> None: # robrandao: TODO
        await self.handle(context, "TeamsMessageSoftDelete", self.default_next_event(context))

    async def _on_teams_members_added(context: TurnContext) -> None:
        await self.handle(context, "TeamsMembersAdded", self.default_next_event(context))

    async def _on_teams_members_removed(context: TurnContext) -> None:
        if "TeamsMembersRemoved" in self.handlers and len(self.handlers["TeamsMembersRemoved"]) > 0:
            await self.handle(context, "TeamsMembersRemoved", self.default_next_event(context))
        else:
            await self.handle(context, "MembersRemoved", self.default_next_event(context))

    async def _on_teams_channel_created(context: TurnContext) -> None:
        await self.handle(context, "TeamsChannelCreated", self.default_next_event(context))

    async def _on_teams_channel_deleted(context: TurnContext) -> None:
        await self.handle(context, "TeamsChannelDeleted", self.default_next_event(context))

    async def _on_teams_channel_renamed(context: TurnContext) -> None:
        await self.handle(context, "TeamsChannelRenamed", self.default_next_event(context))

    async def _on_teams_team_archived(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamArchived", self.default_next_event(context))

    async def _on_teams_team_deleted(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamDeleted", self.default_next_event(context))

    async def _on_teams_team_hard_deleted(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamHardDeleted", self.default_next_event(context))

    async def _on_teams_channel_restored(context: TurnContext) -> None:
        await self.handle(context, "TeamsChannelRestored", self.default_next_event(context))

    async def _on_teams_team_renamed(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamRenamed", self.default_next_event(context))

    async def _on_teams_team_restored(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamRestored", self.default_next_event(context))

    async def _on_teams_team_unarchived(context: TurnContext) -> None:
        await self.handle(context, "TeamsTeamUnarchived", self.default_next_event(context))

    async def on_teams_message_undelete_event(
        self,
        handler: Awaitable[[TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsMessageUndelete", create_callback(handler))
    
    async def on_teams_message_edit_event(
        self,
        handler: Awaitable[[TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsMessageEdit", create_callback(handler))
    
    async def on_teams_message_soft_delete_event(
        self,
        handler: Awaitable[[TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("onTeamsMessageSoftDelete", create_callback(handler)) # robrandao: TODO -> ??
    
    async def on_teams_members_added_event(
        self,
        handler: Awaitable[[list[TeamsChannelAccount], TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
            teams_channel_data = parseTeamsChannelData(context.activity.channel_data)
            await handler(context.activity.membersAdded or [], TeamInfo(teams_channel_data.team), context, next)
        return self.on("TeamsMembersAdded", callback)
    
    async def on_teams_members_removed_event(
        self,
        handler: Awaitable[[list[TeamsChannelAccount], TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
            teams_channel_data = parseTeamsChannelData(context.activity.channel_data)
            await handler(context.activity.membersRemoved or [], TeamInfo(teams_channel_data.team), context, next)
        return self.on("TeamsMembersRemoved", callback)
    
    async def on_teams_channel_created_event(
        self,
        handler: Awaitable[[ChannelInfo, TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsChannelCreated", create_callback_with_channel_info(handler))
    
    async def on_teams_channel_deleted_event(
        self,
        handler: Awaitable[[ChannelInfo, TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsChannelDeleted", create_callback_with_channel_info(handler))
    
    async def on_teams_channel_renamed_event(
        self,
        handler: Awaitable[[ChannelInfo, TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsChannelRenamed", create_callback_with_channel_info(handler))

    async def on_teams_team_archived_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamArchived", create_callback_with_team_info(handler))
    
    async def on_teams_team_deleted_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamDeleted", create_callback_with_team_info(handler))

    async def on_teams_team_hard_deleted_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamHardDeleted", create_callback_with_team_info(handler))
    
    async def on_teams_channel_restored_event(
        self,
        handler: Awaitable[[ChannelInfo, TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsChannelRestored", create_callback_with_channel_info(handler))

    async def on_teams_team_renamed_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamRenamed", create_callback_with_team_info(handler))

    async def on_teams_team_restored_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamRestored", create_callback_with_team_info(handler))

    async def on_teams_team_unarchived_event(
        self,
        handler: Awaitable[[TeamInfo, TurnContext, Awaitable[None, None]]]
    ) -> TeamsActivityHandler:
        return self.on("TeamsTeamUnarchived", create_callback_with_team_info(handler))

    async def _dispatch_event_activity(self, context: TurnContext) -> None: # robrandao: TODO -> return type???

        if context.activity.channel_id == MS_TEAMS:
            handler_map = {
                "application/vnd.microsoft.readReceipt": self._on_teams_read_receipt,
                "application/vnd.microsoft.meetingStart": self._on_teams_meeting_start,
                "application/vnd.microsoft.meetingEnd": self._on_teams_meeting_end,
                "application/vnd.microsoft.meetingParticipantJoin": self._on_teams_meeting_participants_join,
                "application/vnd.microsoft.meetingParticipantLeave": self._on_teams_meeting_participants_leave,
            }
            resolved_handler = handler_map.get(context.activity.name)

            if resolved_handler:
                return await resolved_handler(context)
            else:
                return await super()._dispatch_event_activity(context)
            
    async def _on_teams_meeting_start(self, context: TurnContext) -> None:
        await self.handle(context, "TeamsMeetingStart", self.default_next_event(context))

    async def _on_teams_meeting_end(self, context: TurnContext) -> None:
        await self.handle(context, "TeamsMeetingEnd", self.default_next_event(context))

    async def _on_teams_read_receipt(self, context: TurnContext) -> None:
        await self.handle(context, "TeamsReadReceipt", self.default_next_event(context))

    async def _on_teams_meeting_participants_join(self, context: TurnContext) -> None:
        await self.handle(context, "TeamsMeetingParticipantsJoin", self.default_next_event(context))

    async def _on_teams_meeting_participants_leave(self, context: TurnContext) -> None:
        await self.handle(context, "TeamsMeetingParticipantsLeave", self.default_next_event(context))

    async def on_teams_meeting_start_event(
        self,
        handler: Awaitable[[MeetingStartEventDetails, TurnContext, Awaitable[None, None]], None]
    ) -> TeamsActivityHandler:
        async def callback(context: TurnContext, next: Awaitable[None, None]) -> None:
            meeting = TeamsMeetingStartT.parse(context.activity.value)
            await handler( # robrandao: TODO
                MeetingStartEventDetails(
                    id=meeting.meeting_id,
                    meeting_time=meeting.meeting_time,
                    join_url=meeting.join_url,
                    subject=meeting.subject,
                    organizer=TeamsMeetingMember.parse_obj(meeting.organizer) if meeting.organizer else None,
                    participants=[TeamsMeetingMember.parse_obj(p) for p in meeting.participants] if meeting.participants else []
                ),
                context,
                next
            )
            meeting_info = MeetingStartEventDetails(context.activity.value)
            await handler(meeting_info, context, next)
        return self.on("TeamsMeetingStart", create_callback_with_meeting_info(handler))