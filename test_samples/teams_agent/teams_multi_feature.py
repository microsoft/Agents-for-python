import json
from os import getenv

from msagents.hosting.core import MessageFactory, TurnContext
from msagents.activity import ChannelAccount, Attachment
from msagents.activity.teams import (
    TaskModuleResponse,
    TaskModuleTaskInfo,
    TaskModuleRequest,
)
from msagents.hosting.teams import (
    TeamsActivityHandler,
    TeamsInfo,
)

from helpers.task_module_response_factory import TaskModuleResponseFactory
from helpers.task_module_ids import TaskModuleIds
from helpers.ui_settings import UISettings
from helpers.task_module_ui_constants import TaskModuleUIConstants


class TeamsMultiFeature(TeamsActivityHandler):
    """Teams handler implementing multiple advanced Teams features"""

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Welcome to the Teams Multi-Feature demo!"
                )
                await self._send_help_card(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip() if turn_context.activity.text else ""

        if "help" in text.lower():
            await self._send_help_card(turn_context)
        elif "user profile" in text.lower():
            await self._send_user_profile_card(turn_context)
        elif "restaurant" in text.lower():
            await self._send_restaurant_card(turn_context)
        elif "task" in text.lower():
            await self._send_task_module_card(turn_context)
        elif "youtube" in text.lower():
            await self._send_youtube_card(turn_context)
        else:
            await turn_context.send_activity(
                MessageFactory.text(
                    "Type 'help' to see available commands, or "
                    "'user profile', 'restaurant', 'task', or 'youtube'"
                )
            )

    async def on_teams_task_module_fetch(
        self, turn_context: TurnContext, task_module_request: TaskModuleRequest
    ) -> TaskModuleResponse:
        base_url = getenv("BASE_URL")
        # Handle task module requests
        task_module_type = task_module_request.data.get("data")
        task_info: TaskModuleTaskInfo = None

        if task_module_type:
            task_module_type = task_module_type.lower()

        if task_module_type == TaskModuleIds.YouTube.lower():
            task_info = self._set_task_info(TaskModuleUIConstants.YouTube)
            task_info.url = task_info.fallback_url = f"{base_url}/Youtube"
        elif task_module_type == TaskModuleIds.AdaptiveCard.lower():
            task_info = self._set_task_info(TaskModuleUIConstants.AdaptiveCard)
            task_info.card = self._get_adaptive_card_content()
        elif task_module_type == TaskModuleIds.CustomForm.lower():
            task_info = self._set_task_info(TaskModuleUIConstants.CustomForm)
            task_info.url = task_info.fallback_url = f"{base_url}/CustomForm"

        response = TaskModuleResponseFactory.to_task_module_response(task_info)

        return response

    async def on_teams_task_module_submit(
        self, turn_context: TurnContext, task_module_request
    ):
        # Handle task module submissions
        data = task_module_request.data
        message = f"Received task module submission: {json.dumps(data)}"
        await turn_context.send_activity(MessageFactory.text(message))
        return TaskModuleResponseFactory.create_message_response(message)

    async def _send_help_card(self, turn_context: TurnContext):
        """Send a help card with available commands"""
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Teams Multi-Feature Demo - Available Commands",
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "user profile", "value": "Show user profile card"},
                        {"title": "restaurant", "value": "Show restaurant card"},
                        {"title": "task", "value": "Show task module card"},
                        {"title": "youtube", "value": "Show YouTube card"},
                    ],
                },
            ],
        }

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=card_data
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_user_profile_card(self, turn_context: TurnContext):
        """Send a user profile card"""
        try:
            # Get the current user info
            member = await TeamsInfo.get_member(
                turn_context, turn_context.activity.from_property.id
            )

            card_data = {
                "type": "AdaptiveCard",
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "Medium",
                        "weight": "Bolder",
                        "text": "User Profile",
                    },
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "Image",
                                        "style": "Person",
                                        "size": "Small",
                                    }
                                ],
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "weight": "Bolder",
                                        "text": member.name,
                                        "wrap": True,
                                    },
                                    {
                                        "type": "TextBlock",
                                        "spacing": "None",
                                        "text": f"Email: {member.email or 'Not available'}",
                                        "wrap": True,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            }

            attachment = Attachment(
                content_type="application/vnd.microsoft.card.adaptive",
                content=card_data,
            )

            await turn_context.send_activity(MessageFactory.attachment(attachment))

        except Exception as e:
            await turn_context.send_activity(f"Error retrieving user profile: {str(e)}")

    async def _send_restaurant_card(self, turn_context: TurnContext):
        """Send a restaurant card example"""
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Restaurant Recommendation",
                },
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {
                                    "type": "Image",
                                    "size": "Small",
                                    "url": "https://adaptivecards.io/images/Contoso.png",
                                }
                            ],
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "weight": "Bolder",
                                    "text": "Contoso Cafe",
                                    "wrap": True,
                                },
                                {
                                    "type": "TextBlock",
                                    "spacing": "None",
                                    "text": "⭐⭐⭐⭐★ (4.2) · $$",
                                    "wrap": True,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": "Italian cuisine in a casual atmosphere",
                    "wrap": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Menu",
                    "url": "https://example.com/menu",
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "Order Online",
                    "url": "https://example.com/order",
                },
            ],
        }

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=card_data
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_task_module_card(self, turn_context: TurnContext):
        """Send a card that opens a task module"""
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Task Module Demos",
                },
                {
                    "type": "TextBlock",
                    "text": "Click the buttons below to open different types of task modules",
                    "wrap": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Adaptive Card Form",
                    "data": {
                        "msteams": {"type": "task/fetch"},
                        "data": "adaptiveCard",
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "YouTube Video",
                    "data": {
                        "msteams": {"type": "task/fetch"},
                        "data": "Youtube",
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "Custom Form",
                    "data": {
                        "msteams": {"type": "task/fetch"},
                        "data": "customForm",
                    },
                },
            ],
        }

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=card_data
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_youtube_card(self, turn_context: TurnContext):
        """Send a card with a YouTube video"""
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Microsoft Teams",
                },
                {
                    "type": "TextBlock",
                    "text": "Watch this video to learn more about Microsoft Teams",
                    "wrap": True,
                },
                {
                    "type": "Image",
                    "url": "https://i.ytimg.com/vi/X8krAMdGvCQ/maxresdefault.jpg",
                    "size": "Large",
                    "selectAction": {
                        "type": "Action.Submit",
                        "title": "Watch Video",
                        "data": {
                            "msteams": {"type": "task/fetch"},
                            "data": "Youtube",
                        },
                    },
                },
            ],
        }

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=card_data
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment))

    def _get_adaptive_card_content(self):
        """Get a basic adaptive card content"""
        content = {
            "version": "1.3",
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Enter Text Here",
                    "weight": "bolder",
                    "isSubtle": False,
                },
                {
                    "type": "Input.Text",
                    "id": "usertext",
                    "spacing": "none",
                    "isMultiLine": "true",
                    "placeholder": "add some text and submit",
                },
            ],
            "actions": [{"type": "Action.Submit", "title": "Submit"}],
        }

        # TODO: Fix card creation
        return Attachment.model_validate(
            {
                "content_type": "application/vnd.microsoft.card.adaptive",
                "content": content,
            }
        )

    def _set_task_info(self, ui_constans: UISettings) -> TaskModuleTaskInfo:
        """Set task info for the task module"""
        task_info = TaskModuleTaskInfo(
            title=ui_constans.title, height=ui_constans.height, width=ui_constans.width
        )

        return task_info
