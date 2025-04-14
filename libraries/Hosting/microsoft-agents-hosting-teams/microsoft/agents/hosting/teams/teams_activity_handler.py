"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import json
from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union

from microsoft.agents.builder import ActivityHandler, TurnContext
from microsoft.agents.builder.agent import Agent
from microsoft.agents.core.models import (
    Activity,
    InvokeResponse,
    ChannelAccount,
    ActivityTypes,
    ResourceResponse,
)

from microsoft.agents.core.models.teams import (
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
)

from microsoft.agents.connector.teams.teams_connector_client import TeamsConnectorClient


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
        run_events = True
        try:
            if (
                not turn_context.activity.name
                and turn_context.activity.channel_id == "msteams"
            ):
                return await self.handle_teams_card_action_invoke(turn_context)
            else:
                name = turn_context.activity.name
                value = turn_context.activity.value

                if name == "config/fetch":
                    return self._create_invoke_response(
                        await self.handle_teams_config_fetch(turn_context, value)
                    )
                elif name == "config/submit":
                    return self._create_invoke_response(
                        await self.handle_teams_config_submit(turn_context, value)
                    )
                elif name == "fileConsent/invoke":
                    return self._create_invoke_response(
                        await self.handle_teams_file_consent(turn_context, value)
                    )
                elif name == "actionableMessage/executeAction":
                    await self.handle_teams_o365_connector_card_action(
                        turn_context, value
                    )
                    return self._create_invoke_response()
                elif name == "composeExtension/queryLink":
                    return self._create_invoke_response(
                        await self.handle_teams_app_based_link_query(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/anonymousQueryLink":
                    return self._create_invoke_response(
                        await self.handle_teams_anonymous_app_based_link_query(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/query":
                    query = self._parse_messaging_extension_query(value)
                    return self._create_invoke_response(
                        await self.handle_teams_messaging_extension_query(
                            turn_context, query
                        )
                    )
                elif name == "composeExtension/selectItem":
                    return self._create_invoke_response(
                        await self.handle_teams_messaging_extension_select_item(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/submitAction":
                    return self._create_invoke_response(
                        await self.handle_teams_messaging_extension_submit_action_dispatch(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/fetchTask":
                    return self._create_invoke_response(
                        await self.handle_teams_messaging_extension_fetch_task(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/querySettingUrl":
                    return self._create_invoke_response(
                        await self.handle_teams_messaging_extension_configuration_query_setting_url(
                            turn_context, value
                        )
                    )
                elif name == "composeExtension/setting":
                    await self.handle_teams_messaging_extension_configuration_setting(
                        turn_context, value
                    )
                    return self._create_invoke_response()
                elif name == "composeExtension/onCardButtonClicked":
                    await self.handle_teams_messaging_extension_card_button_clicked(
                        turn_context, value
                    )
                    return self._create_invoke_response()
                elif name == "task/fetch":
                    return self._create_invoke_response(
                        await self.handle_teams_task_module_fetch(turn_context, value)
                    )
                elif name == "task/submit":
                    return self._create_invoke_response(
                        await self.handle_teams_task_module_submit(turn_context, value)
                    )
                elif name == "tab/fetch":
                    return self._create_invoke_response(
                        await self.handle_teams_tab_fetch(turn_context, value)
                    )
                elif name == "tab/submit":
                    return self._create_invoke_response(
                        await self.handle_teams_tab_submit(turn_context, value)
                    )
                else:
                    run_events = False
                    return await super().on_invoke_activity(turn_context)
        except Exception as err:
            if str(err) == "NotImplemented":
                return InvokeResponse(status=int(HTTPStatus.NOT_IMPLEMENTED))
            elif str(err) == "BadRequest":
                return InvokeResponse(status=int(HTTPStatus.BAD_REQUEST))
            raise
        finally:
            if run_events:
                self._default_next_event(turn_context)()

    async def handle_teams_card_action_invoke(
        self, turn_context: TurnContext
    ) -> InvokeResponse:
        """
        Handles card action invoke.

        :param turn_context: The context object for the turn.
        :return: An InvokeResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_config_fetch(
        self, turn_context: TurnContext, config_data: Any
    ) -> ConfigResponse:
        """
        Handles config fetch.

        :param turn_context: The context object for the turn.
        :param config_data: The config data.
        :return: A ConfigResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_config_submit(
        self, turn_context: TurnContext, config_data: Any
    ) -> ConfigResponse:
        """
        Handles config submit.

        :param turn_context: The context object for the turn.
        :param config_data: The config data.
        :return: A ConfigResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_file_consent(
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
            return await self.handle_teams_file_consent_accept(
                turn_context, file_consent_card_response
            )
        elif file_consent_card_response.action == "decline":
            return await self.handle_teams_file_consent_decline(
                turn_context, file_consent_card_response
            )
        else:
            raise ValueError("BadRequest")

    async def handle_teams_file_consent_accept(
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

    async def handle_teams_file_consent_decline(
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

    async def handle_teams_o365_connector_card_action(
        self, turn_context: TurnContext, query: O365ConnectorCardActionQuery
    ) -> None:
        """
        Handles O365 connector card action.

        :param turn_context: The context object for the turn.
        :param query: The O365 connector card action query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_signin_verify_state(
        self, turn_context: TurnContext, query: SigninStateVerificationQuery
    ) -> None:
        """
        Handles sign-in verify state.

        :param turn_context: The context object for the turn.
        :param query: The sign-in state verification query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_signin_token_exchange(
        self, turn_context: TurnContext, query: SigninStateVerificationQuery
    ) -> None:
        """
        Handles sign-in token exchange.

        :param turn_context: The context object for the turn.
        :param query: The sign-in state verification query.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_app_based_link_query(
        self, turn_context: TurnContext, query: AppBasedLinkQuery
    ) -> MessagingExtensionResponse:
        """
        Handles app-based link query.

        :param turn_context: The context object for the turn.
        :param query: The app-based link query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_anonymous_app_based_link_query(
        self, turn_context: TurnContext, query: AppBasedLinkQuery
    ) -> MessagingExtensionResponse:
        """
        Handles anonymous app-based link query.

        :param turn_context: The context object for the turn.
        :param query: The app-based link query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_query(
        self, turn_context: TurnContext, query: MessagingExtensionQuery
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension query.

        :param turn_context: The context object for the turn.
        :param query: The messaging extension query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_select_item(
        self, turn_context: TurnContext, query: Any
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension select item.

        :param turn_context: The context object for the turn.
        :param query: The query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_submit_action_dispatch(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension submit action dispatch.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        if action.message_preview_action:
            if action.message_preview_action == "edit":
                return await self.handle_teams_messaging_extension_message_preview_edit(
                    turn_context, action
                )
            elif action.message_preview_action == "send":
                return await self.handle_teams_messaging_extension_message_preview_send(
                    turn_context, action
                )
            else:
                raise ValueError("BadRequest")
        else:
            return await self.handle_teams_messaging_extension_submit_action(
                turn_context, action
            )

    async def handle_teams_messaging_extension_submit_action(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension submit action.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_message_preview_edit(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension message preview edit.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_message_preview_send(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension message preview send.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_fetch_task(
        self, turn_context: TurnContext, action: MessagingExtensionAction
    ) -> MessagingExtensionActionResponse:
        """
        Handles messaging extension fetch task.

        :param turn_context: The context object for the turn.
        :param action: The messaging extension action.
        :return: A MessagingExtensionActionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_configuration_query_setting_url(
        self, turn_context: TurnContext, query: MessagingExtensionQuery
    ) -> MessagingExtensionResponse:
        """
        Handles messaging extension configuration query setting URL.

        :param turn_context: The context object for the turn.
        :param query: The messaging extension query.
        :return: A MessagingExtensionResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_configuration_setting(
        self, turn_context: TurnContext, settings: Any
    ) -> None:
        """
        Handles messaging extension configuration setting.

        :param turn_context: The context object for the turn.
        :param settings: The settings.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_messaging_extension_card_button_clicked(
        self, turn_context: TurnContext, card_data: Any
    ) -> None:
        """
        Handles messaging extension card button clicked.

        :param turn_context: The context object for the turn.
        :param card_data: The card data.
        :return: None
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_task_module_fetch(
        self, turn_context: TurnContext, task_module_request: TaskModuleRequest
    ) -> TaskModuleResponse:
        """
        Handles task module fetch.

        :param turn_context: The context object for the turn.
        :param task_module_request: The task module request.
        :return: A TaskModuleResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_task_module_submit(
        self, turn_context: TurnContext, task_module_request: TaskModuleRequest
    ) -> TaskModuleResponse:
        """
        Handles task module submit.

        :param turn_context: The context object for the turn.
        :param task_module_request: The task module request.
        :return: A TaskModuleResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_tab_fetch(
        self, turn_context: TurnContext, tab_request: TabRequest
    ) -> TabResponse:
        """
        Handles tab fetch.

        :param turn_context: The context object for the turn.
        :param tab_request: The tab request.
        :return: A TabResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def handle_teams_tab_submit(
        self, turn_context: TurnContext, tab_submit: TabSubmit
    ) -> TabResponse:
        """
        Handles tab submit.

        :param turn_context: The context object for the turn.
        :param tab_submit: The tab submit.
        :return: A TabResponse.
        """
        raise NotImplementedError("NotImplemented")

    async def dispatch_conversation_update_activity(
        self, turn_context: TurnContext
    ) -> None:
        """
        Dispatches conversation update activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = self._parse_teams_channel_data(
                turn_context.activity.channel_data
            )

            if (
                turn_context.activity.members_added
                and len(turn_context.activity.members_added) > 0
            ):
                return await self.on_teams_members_added(turn_context)

            if (
                turn_context.activity.members_removed
                and len(turn_context.activity.members_removed) > 0
            ):
                return await self.on_teams_members_removed(turn_context)

            if not channel_data or "eventType" not in channel_data:
                return await super().dispatch_conversation_update_activity(turn_context)

            event_type = channel_data.get("eventType")

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
            else:
                return await super().dispatch_conversation_update_activity(turn_context)
        else:
            return await super().dispatch_conversation_update_activity(turn_context)

    async def dispatch_message_update_activity(self, turn_context: TurnContext) -> None:
        """
        Dispatches message update activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = self._parse_teams_channel_data(
                turn_context.activity.channel_data
            )
            event_type = channel_data.get("eventType") if channel_data else None

            if event_type == "undeleteMessage":
                return await self.on_teams_message_undelete(turn_context)
            elif event_type == "editMessage":
                return await self.on_teams_message_edit(turn_context)
            else:
                return await super().dispatch_message_update_activity(turn_context)
        else:
            return await super().dispatch_message_update_activity(turn_context)

    async def dispatch_message_delete_activity(self, turn_context: TurnContext) -> None:
        """
        Dispatches message delete activity.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if turn_context.activity.channel_id == "msteams":
            channel_data = self._parse_teams_channel_data(
                turn_context.activity.channel_data
            )
            event_type = channel_data.get("eventType") if channel_data else None

            if event_type == "softDeleteMessage":
                return await self.on_teams_message_soft_delete(turn_context)
            else:
                return await super().dispatch_message_delete_activity(turn_context)
        else:
            return await super().dispatch_message_delete_activity(turn_context)

    async def on_teams_message_undelete(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message undelete.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsMessageUndelete", self._default_next_event(turn_context)
        )

    async def on_teams_message_edit(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message edit.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsMessageEdit", self._default_next_event(turn_context)
        )

    async def on_teams_message_soft_delete(self, turn_context: TurnContext) -> None:
        """
        Handles Teams message soft delete.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context,
            "TeamsMessageSoftDelete",
            self._default_next_event(turn_context),
        )

    async def on_teams_members_added(self, turn_context: TurnContext) -> None:
        """
        Handles Teams members added.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if (
            hasattr(self, "handlers")
            and "TeamsMembersAdded" in self.handlers
            and self.handlers["TeamsMembersAdded"]
        ):
            if not turn_context.activity or not turn_context.activity.members_added:
                raise ValueError("OnTeamsMemberAdded: context.activity is undefined")

            for i, channel_account in enumerate(turn_context.activity.members_added):
                if (
                    hasattr(channel_account, "given_name")
                    or hasattr(channel_account, "surname")
                    or hasattr(channel_account, "email")
                    or hasattr(channel_account, "user_principal_name")
                    or (
                        turn_context.activity.recipient
                        and turn_context.activity.recipient.id == channel_account.id
                    )
                ):
                    continue

                try:
                    turn_context.activity.members_added[i] = (
                        await TeamsConnectorClient.get_member(
                            turn_context.activity, channel_account.id
                        )
                    )
                except Exception as err:
                    err_body = getattr(err, "body", None)
                    err_code = (
                        (err_body and err_body.get("error", {}).get("code", ""))
                        if err_body
                        else ""
                    )

                    if err_code == "ConversationNotFound":
                        teams_channel_account = TeamsChannelAccount(
                            id=channel_account.id,
                            name=channel_account.name,
                            aad_object_id=channel_account.aad_object_id,
                            role=channel_account.role,
                        )
                        turn_context.activity.members_added[i] = teams_channel_account
                    else:
                        raise

            await self._handle_event(
                turn_context,
                "TeamsMembersAdded",
                self._default_next_event(turn_context),
            )
        else:
            await self._handle_event(
                turn_context, "MembersAdded", self._default_next_event(turn_context)
            )

    async def on_teams_members_removed(self, turn_context: TurnContext) -> None:
        """
        Handles Teams members removed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        if (
            hasattr(self, "handlers")
            and "TeamsMembersRemoved" in self.handlers
            and self.handlers["TeamsMembersRemoved"]
        ):
            await self._handle_event(
                turn_context,
                "TeamsMembersRemoved",
                self._default_next_event(turn_context),
            )
        else:
            await self._handle_event(
                turn_context, "MembersRemoved", self._default_next_event(turn_context)
            )

    async def on_teams_channel_created(self, turn_context: TurnContext) -> None:
        """
        Handles Teams channel created.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsChannelCreated", self._default_next_event(turn_context)
        )

    async def on_teams_channel_deleted(self, turn_context: TurnContext) -> None:
        """
        Handles Teams channel deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsChannelDeleted", self._default_next_event(turn_context)
        )

    async def on_teams_channel_renamed(self, turn_context: TurnContext) -> None:
        """
        Handles Teams channel renamed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsChannelRenamed", self._default_next_event(turn_context)
        )

    async def on_teams_team_archived(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team archived.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamArchived", self._default_next_event(turn_context)
        )

    async def on_teams_team_deleted(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamDeleted", self._default_next_event(turn_context)
        )

    async def on_teams_team_hard_deleted(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team hard deleted.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamHardDeleted", self._default_next_event(turn_context)
        )

    async def on_teams_channel_restored(self, turn_context: TurnContext) -> None:
        """
        Handles Teams channel restored.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsChannelRestored", self._default_next_event(turn_context)
        )

    async def on_teams_team_renamed(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team renamed.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamRenamed", self._default_next_event(turn_context)
        )

    async def on_teams_team_restored(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team restored.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamRestored", self._default_next_event(turn_context)
        )

    async def on_teams_team_unarchived(self, turn_context: TurnContext) -> None:
        """
        Handles Teams team unarchived.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsTeamUnarchived", self._default_next_event(turn_context)
        )

    async def dispatch_event_activity(self, turn_context: TurnContext) -> None:
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

        return await super().dispatch_event_activity(turn_context)

    async def on_teams_meeting_start(self, turn_context: TurnContext) -> None:
        """
        Handles Teams meeting start.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsMeetingStart", self._default_next_event(turn_context)
        )

    async def on_teams_meeting_end(self, turn_context: TurnContext) -> None:
        """
        Handles Teams meeting end.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsMeetingEnd", self._default_next_event(turn_context)
        )

    async def on_teams_read_receipt(self, turn_context: TurnContext) -> None:
        """
        Handles Teams read receipt.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context, "TeamsReadReceipt", self._default_next_event(turn_context)
        )

    async def on_teams_meeting_participants_join(
        self, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting participants join.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context,
            "TeamsMeetingParticipantsJoin",
            self._default_next_event(turn_context),
        )

    async def on_teams_meeting_participants_leave(
        self, turn_context: TurnContext
    ) -> None:
        """
        Handles Teams meeting participants leave.

        :param turn_context: The context object for the turn.
        :return: None
        """
        await self._handle_event(
            turn_context,
            "TeamsMeetingParticipantsLeave",
            self._default_next_event(turn_context),
        )

    def on_teams_message_undelete_event(
        self,
        handler: Callable[
            [TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams message undelete event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMessageUndelete", lambda context, next_: handler(context, next_)
        )

    def on_teams_message_edit_event(
        self,
        handler: Callable[
            [TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams message edit event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMessageEdit", lambda context, next_: handler(context, next_)
        )

    def on_teams_message_soft_delete_event(
        self,
        handler: Callable[
            [TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams message soft delete event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMessageSoftDelete", lambda context, next_: handler(context, next_)
        )

    def on_teams_members_added_event(
        self,
        handler: Callable[
            [
                List[TeamsChannelAccount],
                TeamInfo,
                TurnContext,
                Callable[[], Awaitable[None]],
            ],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams members added event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMembersAdded",
            lambda context, next_: handler(
                context.activity.members_added or [],
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_members_removed_event(
        self,
        handler: Callable[
            [
                List[TeamsChannelAccount],
                TeamInfo,
                TurnContext,
                Callable[[], Awaitable[None]],
            ],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams members removed event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMembersRemoved",
            lambda context, next_: handler(
                context.activity.members_removed or [],
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_channel_created_event(
        self,
        handler: Callable[
            [ChannelInfo, TeamInfo, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams channel created event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsChannelCreated",
            lambda context, next_: handler(
                self._get_channel_info(context.activity.channel_data),
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_channel_deleted_event(
        self,
        handler: Callable[
            [ChannelInfo, TeamInfo, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams channel deleted event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsChannelDeleted",
            lambda context, next_: handler(
                self._get_channel_info(context.activity.channel_data),
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_channel_renamed_event(
        self,
        handler: Callable[
            [ChannelInfo, TeamInfo, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams channel renamed event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsChannelRenamed",
            lambda context, next_: handler(
                self._get_channel_info(context.activity.channel_data),
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_team_archived_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team archived event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamArchived",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_team_deleted_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team deleted event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamDeleted",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_team_hard_deleted_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team hard deleted event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamHardDeleted",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_channel_restored_event(
        self,
        handler: Callable[
            [ChannelInfo, TeamInfo, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams channel restored event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsChannelRestored",
            lambda context, next_: handler(
                self._get_channel_info(context.activity.channel_data),
                self._get_teams_info(context.activity.channel_data),
                context,
                next_,
            ),
        )

    def on_teams_team_renamed_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team renamed event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamRenamed",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_team_restored_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team restored event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamRestored",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_team_unarchived_event(
        self,
        handler: Callable[
            [TeamInfo, TurnContext, Callable[[], Awaitable[None]]], Awaitable[None]
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams team unarchived event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsTeamUnarchived",
            lambda context, next_: handler(
                self._get_teams_info(context.activity.channel_data), context, next_
            ),
        )

    def on_teams_meeting_start_event(
        self,
        handler: Callable[
            [MeetingStartEventDetails, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams meeting start event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMeetingStart",
            lambda context, next_: handler(
                self._parse_teams_meeting_start(context.activity.value), context, next_
            ),
        )

    def on_teams_meeting_end_event(
        self,
        handler: Callable[
            [MeetingEndEventDetails, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams meeting end event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMeetingEnd",
            lambda context, next_: handler(
                self._parse_teams_meeting_end(context.activity.value), context, next_
            ),
        )

    def on_teams_read_receipt_event(
        self,
        handler: Callable[
            [ReadReceiptInfo, TurnContext, Callable[[], Awaitable[None]]],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams read receipt event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsReadReceipt",
            lambda context, next_: handler(
                ReadReceiptInfo(context.activity.value.get("lastReadMessageId", "")),
                context,
                next_,
            ),
        )

    def on_teams_meeting_participants_join_event(
        self,
        handler: Callable[
            [
                MeetingParticipantsEventDetails,
                TurnContext,
                Callable[[], Awaitable[None]],
            ],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams meeting participants join event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMeetingParticipantsJoin",
            lambda context, next_: handler(
                self._parse_teams_meeting_participants_event(context.activity.value),
                context,
                next_,
            ),
        )

    def on_teams_meeting_participants_leave_event(
        self,
        handler: Callable[
            [
                MeetingParticipantsEventDetails,
                TurnContext,
                Callable[[], Awaitable[None]],
            ],
            Awaitable[None],
        ],
    ) -> "TeamsActivityHandler":
        """
        Registers a handler for Teams meeting participants leave event.

        :param handler: The handler function.
        :return: The TeamsActivityHandler instance.
        """
        return self.on(
            "TeamsMeetingParticipantsLeave",
            lambda context, next_: handler(
                self._parse_teams_meeting_participants_event(context.activity.value),
                context,
                next_,
            ),
        )

    def _create_invoke_response(self, body: Any = None) -> InvokeResponse:
        """
        Creates an invoke response.

        :param body: The response body.
        :return: An InvokeResponse.
        """
        return InvokeResponse(
            status=int(HTTPStatus.OK),
            body=body,
        )

    def _parse_messaging_extension_query(self, value: Any) -> MessagingExtensionQuery:
        """
        Parses a messaging extension query from the activity value.

        :param value: The activity value.
        :return: A MessagingExtensionQuery.
        """
        if isinstance(value, dict):
            return MessagingExtensionQuery(**value)
        return value

    def _parse_teams_channel_data(self, channel_data: Any) -> Dict[str, Any]:
        """
        Parses Teams channel data.

        :param channel_data: The channel data.
        :return: A dictionary containing the parsed channel data.
        """
        if not channel_data:
            return {}

        if isinstance(channel_data, str):
            try:
                return json.loads(channel_data)
            except:
                return {}

        return channel_data if isinstance(channel_data, dict) else {}

    def _get_teams_info(self, channel_data: Any) -> TeamInfo:
        """
        Gets Teams info from channel data.

        :param channel_data: The channel data.
        :return: A TeamInfo object.
        """
        data = self._parse_teams_channel_data(channel_data)
        return data.get("team", {})

    def _get_channel_info(self, channel_data: Any) -> ChannelInfo:
        """
        Gets channel info from channel data.

        :param channel_data: The channel data.
        :return: A ChannelInfo object.
        """
        data = self._parse_teams_channel_data(channel_data)
        return data.get("channel", {})

    def _parse_teams_meeting_start(self, value: Any) -> MeetingStartEventDetails:
        """
        Parses Teams meeting start event details.

        :param value: The event value.
        :return: A MeetingStartEventDetails object.
        """
        if not value:
            raise ValueError("Meeting start event value is missing")

        return MeetingStartEventDetails(
            id=value.get("Id", ""),
            join_url=value.get("JoinUrl", ""),
            meeting_type=value.get("MeetingType", ""),
            title=value.get("Title", ""),
            start_time=(
                datetime.fromisoformat(value.get("StartTime"))
                if value.get("StartTime")
                else None
            ),
        )

    def _parse_teams_meeting_end(self, value: Any) -> MeetingEndEventDetails:
        """
        Parses Teams meeting end event details.

        :param value: The event value.
        :return: A MeetingEndEventDetails object.
        """
        if not value:
            raise ValueError("Meeting end event value is missing")

        return MeetingEndEventDetails(
            id=value.get("Id", ""),
            join_url=value.get("JoinUrl", ""),
            meeting_type=value.get("MeetingType", ""),
            title=value.get("Title", ""),
            end_time=(
                datetime.fromisoformat(value.get("EndTime"))
                if value.get("EndTime")
                else None
            ),
        )

    def _parse_teams_meeting_participants_event(
        self, value: Any
    ) -> MeetingParticipantsEventDetails:
        """
        Parses Teams meeting participants event details.

        :param value: The event value.
        :return: A MeetingParticipantsEventDetails object.
        """
        if not value:
            raise ValueError("Meeting participants event value is missing")

        return MeetingParticipantsEventDetails(members=value.get("members", []))

    def _default_next_event(
        self, context: TurnContext
    ) -> Callable[[], Awaitable[None]]:
        """
        Creates a default next event handler.

        :param context: The context object for the turn.
        :return: A callable that returns an awaitable.
        """

        async def next_event():
            # No-op default next event handler
            pass

        return next_event

    async def _handle_event(
        self,
        context: TurnContext,
        event_name: str,
        next_event: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Helper method for handling events.

        :param context: The context object for the turn.
        :param event_name: The name of the event.
        :param next_event: The next event handler.
        :return: None
        """
        if hasattr(self, "handlers") and event_name in self.handlers:
            for handler in self.handlers[event_name]:
                await handler(context, next_event)
        else:
            await next_event()
