"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from http import HTTPStatus
from typing import Any, List

from microsoft.agents.hosting.core import ActivityHandler, TurnContext
from microsoft.agents.activity import (
    InvokeResponse,
    ChannelAccount,
)

from microsoft.agents.activity.teams import (
    AppBasedLinkQuery,
    TeamInfo,
    ChannelInfo,
    ConfigResponse,
    FileConsentCardResponse,
    MeetingEndEventDetails,
    MeetingParticipantsEventDetails,
    MeetingStartEventDetails,
    MessagingExtensionAction,
    MessagingExtensionActionResponse,
    MessagingExtensionQuery,
    MessagingExtensionResponse,
    O365ConnectorCardActionQuery,
    ReadReceiptInfo,
    SigninStateVerificationQuery,
    TabRequest,
    TabResponse,
    TabSubmit,
    TaskModuleRequest,
    TaskModuleResponse,
    TeamsChannelAccount,
    TeamsChannelData,
)

from .teams_info import TeamsInfo


class TeamsActivityHandler(ActivityHandler):
    """
    The TeamsActivityHandler is derived from the ActivityHandler class and adds support for
    Microsoft Teams-specific functionality.
    """

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        """
        Handles invoke activities.

        :param turn_context: The context object for the turn.
        :return: An InvokeResponse.
        """

        try:
            if (
                not turn_context.activity.name
                and turn_context.activity.channel_id == "msteams"
            ):
                return await self.on_teams_card_action_invoke(turn_context)
            else:
                name = turn_context.activity.name
                value = turn_context.activity.value

                if name == "config/fetch":
                    return self._create_invoke_response(
                        await self.on_teams_config_fetch(turn_context, value)
                    )
                elif name == "config/submit":
                    return self._create_invoke_response(
                        await self.on_teams_config_submit(turn_context, value)
                    )
                elif name == "fileConsent/invoke":
                    return self._create_invoke_response(
                        await self.on_teams_file_consent(turn_context, value)
                    )
                elif name == "actionableMessage/executeAction":
                    await self.on_teams_o365_connector_card_action(turn_context, value)
                    return self._create_invoke_response()
                elif name == "composeExtension/queryLink":
                    return self._create_invoke_response(
                        await self.on_teams_app_based_link_query(turn_context, value)
                    )
                elif name == "composeExtension/anonymousQueryLink":
                    return self._create_invoke_response(
                        await self.on_teams_anonymous_app_based_link_query(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/query":
                    query = MessagingExtensionQuery.model_validate(value)
                    return self._create_invoke_response(
                        await self.on_teams_messaging_extension_query(
                            turn_context, query
                        )
                    )
                elif name == "composeExtension/selectItem":
                    return self._create_invoke_response(
                        await self.on_teams_messaging_extension_select_item(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/submitAction":
                    return self._create_invoke_response(
                        await self.on_teams_messaging_extension_submit_action_dispatch(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/fetchTask":
                    return self._create_invoke_response(
                        await self.on_teams_messaging_extension_fetch_task(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/querySettingUrl":
                    return self._create_invoke_response(
                        await self.on_teams_messaging_extension_configuration_query_setting_url(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/setting":
                    await self.on_teams_messaging_extension_configuration_setting(
                        turn_context, value
                    )
                    return self._create_invoke_response()
                elif name == "composeExtension/onCardButtonClicked":
                    await self.on_teams_messaging_extension_card_button_clicked(
                        turn_context, value
                    )
                    return self._create_invoke_response()
                elif name == "task/fetch":
                    task_module_request = TaskModuleRequest.model_validate(value)
                    return self._create_invoke_response(
                        await self.on_teams_task_module_fetch(
                            turn_context, task_module_request
                        )
                    )
                elif name == "task/submit":
                    task_module_request = TaskModuleRequest.model_validate(value)
                    return self._create_invoke_response(
                        await self.on_teams_task_module_submit(
                            turn_context, task_module_request
                        )
                    )
                elif name == "tab/fetch":
                    return self._create_invoke_response(
                        await self.on_teams_tab_fetch(turn_context, value)
                    )
                elif name == "tab/submit":
                    return self._create_invoke_response(
                        await self.on_teams_tab_submit(turn_context, value)
                    )
                else:
                    return await super().on_invoke_activity(turn_context)
        except Exception as err:
            if str(err) == "NotImplemented":
                return InvokeResponse(status=int(HTTPStatus.NOT_IMPLEMENTED))
            elif str(err) == "BadRequest":
                return InvokeResponse(status=int(HTTPStatus.BAD_REQUEST))
            raise

    async def on_teams_card_action_invoke(
        self, turn_context: TurnContext
    ) -> InvokeResponse:
        """
        Handles card action invoke.

        :param turn_context: The context object for the turn.
        :return: An InvokeResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_config_fetch(
        self, turn_context: TurnContext, config_data: Any
    ) -> ConfigResponse:
        """
        Handles config fetch.

        :param turn_context: The context object for the turn.
        :param config_data: The config data.
        :return: A ConfigResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_config_submit(
        self, turn_context: TurnContext, config_data: Any
    ) -> ConfigResponse:
        """
        Handles config submit.

        :param turn_context: The context object for the turn.
        :param config_data: The config data.
        :return: A ConfigResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_file_consent(
        self,
        turn_context: TurnContext,
        file_consent_card_response: FileConsentCardResponse,
    ) -> None:
        """
        Handles file consent.

        :param turn_context: The context object for the turn.
        :param file_consent_card_response: The file consent card response.
        :return: None
        """
        if file_consent_card_response.action == "accept":
            return await self.on_teams_file_consent_accept(
                turn_context, file_consent_card_response
            )
        elif file_consent_card_response.action == "decline":
            return await self.on_teams_file_consent_decline(
                turn_context, file_consent_card_response
            )
        else:
            raise ValueError("BadRequest")

    async def on_teams_file_consent_accept(
        self,
        turn_context: TurnContext,
        file_consent_card_response: FileConsentCardResponse,
    ) -> None:
        """
        Handles file consent accept.

        :param turn_context: The context object for the turn.
        :param file_consent_card_response: The file consent card response.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_file_consent_decline(
        self,
        turn_context: TurnContext,
        file_consent_card_response: FileConsentCardResponse,
    ) -> None:
        """
        Handles file consent decline.

        :param turn_context: The context object for the turn.
        :param file_consent_card_response: The file consent card response.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_o365_connector_card_action(
        self, turn_context: TurnContext, query: O365ConnectorCardActionQuery
    ) -> None:
        """
        Handles O365 connector card action.

        :param turn_context: The context object for the turn.
        :param query: The O365 connector card action query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_signin_verify_state(
        self, turn_context: TurnContext, query: SigninStateVerificationQuery
    ) -> None:
        """
        Handles sign-in verify state.

        :param turn_context: The context object for the turn.
        :param query: The sign-in state verification query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_signin_token_exchange(
        self, turn_context: TurnContext, query: SigninStateVerificationQuery
    ) -> None:
        """
        Handles sign-in token exchange.

        :param turn_context: The context object for the turn.
        :param query: The sign-in state verification query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_app_based_link_query(
        self, turn_context: TurnContext, query: AppBasedLinkQuery
    ) -> MessagingExtensionResponse:
        """
        Handles app-based link query.

        :param turn_context: The context object for the turn.
        :param query: The app-based link query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_anonymous_app_based_link_query(
        self, turn_context: TurnContext, query: AppBasedLinkQuery
    ) -> MessagingExtensionResponse:
        """
        Handles anonymous app-based link query.

        :param turn_context: The context object for the turn.
        :param query: The app-based link query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_query(
        self, turn_context: TurnContext, query: MessagingExtensionQuery
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension query.

        :param turn_context: The context object for the turn.
        :param query: The messaging extension query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_select_item(
        self, turn_context: TurnContext, query: Any
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension select item.

        :param turn_context: The context object for the turn.
        :param query: The query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_submit_action_dispatch(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension submit action dispatch.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        if action.bot_message_preview_action:
            if action.bot_message_preview_action == "edit":
                return await self.on_teams_messaging_extension_message_preview_edit(
                    turn_context, action
                )
            elif action.bot_message_preview_action == "send":
                return await self.on_teams_messaging_extension_message_preview_send(
                    turn_context, action
                )
            else:
                raise ValueError("BadRequest")
        else:
            return await self.on_teams_messaging_extension_submit_action(
                turn_context, action
            )

    async def on_teams_messaging_extension_submit_action(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension submit action.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_message_preview_edit(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension message preview edit.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_message_preview_send(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension message preview send.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_fetch_task(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension fetch task.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_configuration_query_setting_url(
        self, turn_context: TurnContext, query: MessagingExtensionQuery
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension configuration query setting URL.

        :param turn_context: The context object for the turn.
        :param query: The messaging extension query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_configuration_setting(
        self, turn_context: TurnContext, settings: Any
    ) -> None:
        """
        Handles messaging extension configuration setting.

        :param turn_context: The context object for the turn.
        :param settings: The settings.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_messaging_extension_card_button_clicked(
        self, turn_context: TurnContext, card_data: Any
    ) -> None:
        """
        Handles messaging extension card button clicked.

        :param turn_context: The context object for the turn.
        :param card_data: The card data.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_task_module_fetch(
        self, turn_context: TurnContext, task_module_request: TaskModuleRequest
    ) -> TaskModuleResponse:
        """
        Handles task module fetch.

        :param turn_context: The context object for the turn.
        :param task_module_request: The task module request.
        :return: A TaskModuleResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_task_module_submit(
        self, turn_context: TurnContext, task_module_request: TaskModuleRequest
    ) -> TaskModuleResponse:
        """
        Handles task module submit.

        :param turn_context: The context object for the turn.
        :param task_module_request: The task module request.
        :return: A TaskModuleResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_tab_fetch(
        self, turn_context: TurnContext, tab_request: TabRequest
    ) -> TabResponse:
        """
        Handles tab fetch.

        :param turn_context: The context object for the turn.
        :param tab_request: The tab request.
        :return: A TabResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_teams_tab_submit(
        self, turn_context: TurnContext, tab_submit: TabSubmit
    ) -> TabResponse:
        """
        Handles tab submit.

        :param turn_context: The context object for the turn.
        :param tab_submit: The tab submit.
        :return: A TabResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """
        Dispatches conversation update activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = (
                TeamsChannelData.model_validate(turn_context.activity.channel_data)
                if turn_context.activity.channel_data
                else None
            )

            if (
                turn_context.activity.members_added
                and len(turn_context.activity.members_added) > 0
            ):
                return await self.on_teams_members_added_dispatch(
                    turn_context.activity.members_added,
                    channel_data.team if channel_data else None,
                    turn_context,
                )

            if (
                turn_context.activity.members_removed
                and len(turn_context.activity.members_removed) > 0
            ):
                return await self.on_teams_members_removed(turn_context)

            if not channel_data or not channel_data.event_type:
                return await super().on_conversation_update_activity(turn_context)

            event_type = channel_data.event_type

            if event_type == "channelCreated":
                return await self.on_teams_channel_created(turn_context)
            elif event_type == "channelDeleted":
                return await self.on_teams_channel_deleted(turn_context)
            elif event_type == "channelRenamed":
                return await self.on_teams_channel_renamed(turn_context)
            elif event_type == "teamArchived":
                return await self.on_teams_team_archived(turn_context)
            elif event_type == "teamDeleted":
                return await self.on_teams_team_deleted(turn_context)
            elif event_type == "teamHardDeleted":
                return await self.on_teams_team_hard_deleted(turn_context)
            elif event_type == "channelRestored":
                return await self.on_teams_channel_restored(turn_context)
            elif event_type == "teamRenamed":
                return await self.on_teams_team_renamed(turn_context)
            elif event_type == "teamRestored":
                return await self.on_teams_team_restored(turn_context)
            elif event_type == "teamUnarchived":
                return await self.on_teams_team_unarchived(turn_context)

        return await super().on_conversation_update_activity(turn_context)

    async def on_message_update_activity(self, turn_context: TurnContext):
        """
        Dispatches message update activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = channel_data = (
                TeamsChannelData.model_validate(turn_context.activity.channel_data)
                if turn_context.activity.channel_data
                else None
            )

            event_type = channel_data.event_type if channel_data else None

            if event_type == "undeleteMessage":
                return await self.on_teams_message_undelete(turn_context)
            elif event_type == "editMessage":
                return await self.on_teams_message_edit(turn_context)

        return await super().on_message_update_activity(turn_context)

    async def on_message_delete_activity(self, turn_context: TurnContext) -> None:
        """
        Dispatches message delete activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = channel_data = (
                TeamsChannelData.model_validate(turn_context.activity.channel_data)
                if turn_context.activity.channel_data
                else None
            )

            event_type = channel_data.event_type if channel_data else None

            if event_type == "softDeleteMessage":
                return await self.on_teams_message_soft_delete(turn_context)

        return await super().on_message_delete_activity(turn_context)

    async def on_teams_message_undelete(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message undelete.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_message_edit(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message edit.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_message_soft_delete(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message soft delete.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_members_added_dispatch(
        self,
        members_added: List[ChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ) -> None:
        """
        Dispatches processing of Teams members added to the conversation.
        Processes the members_added collection to get full member information when possible.

        :param members_added: The list of members being added to the conversation.
        :param team_info: The team info object.
        :param turn_context: The context object for the turn.
        :return: None
        """
        teams_members_added = []

        for member in members_added:
            # If the member has properties or is the agent/bot being added to the conversation
            if len(member.properties) or (
                turn_context.activity.recipient
                and turn_context.activity.recipient.id == member.id
            ):

                # Convert the ChannelAccount to TeamsChannelAccount
                # TODO: Converter between these two classes
                teams_member = TeamsChannelAccount.model_validate(
                    member.model_dump(by_alias=True, exclude_unset=True)
                )
                teams_members_added.append(teams_member)
            else:
                # Try to get the full member details from Teams
                try:
                    teams_member = await TeamsInfo.get_member(turn_context, member.id)
                    teams_members_added.append(teams_member)
                except Exception as err:
                    # Handle case where conversation is not found
                    if "ConversationNotFound" in str(err):
                        teams_channel_account = TeamsChannelAccount(
                            id=member.id,
                            name=member.name,
                            aad_object_id=getattr(member, "aad_object_id", None),
                            role=getattr(member, "role", None),
                        )
                        teams_members_added.append(teams_channel_account)
                    else:
                        # Propagate any other errors
                        raise

        await self.on_teams_members_added(teams_members_added, team_info, turn_context)

    async def on_teams_members_added(
        self,
        teams_members_added: List[TeamsChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ) -> None:
        """
        Handles Teams members added.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self.on_members_added_activity(teams_members_added, turn_context)

    async def on_teams_members_removed_dispatch(
        self,
        members_removed: List[ChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ) -> None:
        """
        Dispatches processing of Teams members removed from the conversation.
        """
        teams_members_removed = []
        for member in members_removed:
            teams_members_removed.append(
                TeamsChannelAccount.model_validate(
                    member.model_dump(by_alias=True, exclude_unset=True)
                )
            )
        return await self.on_teams_members_removed(
            teams_members_removed, team_info, turn_context
        )

    async def on_teams_members_removed(
        self,
        teams_members_removed: List[TeamsChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ) -> None:
        """
        Handles Teams members removed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self.on_members_removed_activity(teams_members_removed, turn_context)

    async def on_teams_channel_created(
        self, channel_info: ChannelInfo, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams channel created.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_channel_deleted(
        self, channel_info: ChannelInfo, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams channel deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_channel_renamed(
        self, channel_info: ChannelInfo, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams channel renamed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_archived(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team archived.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_deleted(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_hard_deleted(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team hard deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_channel_restored(
        self, channel_info: ChannelInfo, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams channel restored.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_renamed(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team renamed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_restored(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team restored.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_team_unarchived(
        self, team_info: TeamInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams team unarchived.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_event_activity(self, turn_context: TurnContext) -> None:
        """
        Dispatches event activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            if turn_context.activity.name == "application/vnd.microsoft.readReceipt":
                return await self.on_teams_read_receipt(turn_context)
            elif turn_context.activity.name == "application/vnd.microsoft.meetingStart":
                return await self.on_teams_meeting_start(turn_context)
            elif turn_context.activity.name == "application/vnd.microsoft.meetingEnd":
                return await self.on_teams_meeting_end(turn_context)
            elif (
                turn_context.activity.name
                == "application/vnd.microsoft.meetingParticipantJoin"
            ):
                return await self.on_teams_meeting_participants_join(turn_context)
            elif (
                turn_context.activity.name
                == "application/vnd.microsoft.meetingParticipantLeave"
            ):
                return await self.on_teams_meeting_participants_leave(turn_context)

        return await super().on_event_activity(turn_context)

    async def on_teams_meeting_start(
        self, meeting: MeetingStartEventDetails, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting start.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_meeting_end(
        self, meeting: MeetingEndEventDetails, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting end.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_read_receipt(
        self, read_receipt: ReadReceiptInfo, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams read receipt.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_meeting_participants_join(
        self, meeting: MeetingParticipantsEventDetails, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting participants join.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return

    async def on_teams_meeting_participants_leave(
        self, meeting: MeetingParticipantsEventDetails, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting participants leave.

        :param turn_context: The context object for the turn.
        :return: None
        """
        return
