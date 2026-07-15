# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import aiohttp

from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from microsoft_agents.hosting.dialogs.prompts import (
    PromptOptions,
    OAuthPrompt,
    OAuthPromptSettings
)
from microsoft_agents.hosting.core import MessageFactory, UserState, AccessTokenProviderBase

from .create_profile_card import create_profile_card


class UserProfileDialog(ComponentDialog):
    def __init__(self, user_state: UserState, connection_name: str):
        super(UserProfileDialog, self).__init__(UserProfileDialog.__name__)

        self.user_profile_accessor = user_state.create_property("UserProfile")

        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    title="Sign In",
                    text="Please login to your Microsoft account to continue.",
                    end_on_invalid_message=True,
                )
            )
        )

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.oauth_step,       # Add OAuth as first step
                    self.profile_step
                ],
            )
        )
        self.initial_dialog_id = WaterfallDialog.__name__

    @staticmethod
    async def get_user_info(token) -> dict[str, object]:
        """
        Get information about the current user from Microsoft Graph API.
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            async with session.get(
                "https://graph.microsoft.com/v1.0/me", headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                raise Exception(f"Error from Graph API: {response.status} - {error_text}")

    async def oauth_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """First step: Authenticate the user with OAuth."""
        return await step_context.prompt(
            OAuthPrompt.__name__,  # Use the OAuthPrompt we defined
            PromptOptions(
                prompt=MessageFactory.text("Please sign in to continue.")
            )
        )
    
    async def profile_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Second step: Get user profile information using OAuth token and display profile card."""
        # Get the token from the OAuth step
        token_response = step_context.result
        
        if token_response:
            try:
                # Use the token to get user info from Microsoft Graph
                user_info = await self.get_user_info(token_response.token)
                
                # Create and send the profile card
                profile_card = create_profile_card(user_info)
                card_activity = MessageFactory.attachment(profile_card)
                await step_context.context.send_activity(card_activity)
                
                # Send a text message as well
                await step_context.context.send_activity(
                    MessageFactory.text(f"Hello {user_info.get('displayName', 'User')}! Here's your profile information.")
                )
                
            except Exception as e:
                await step_context.context.send_activity(
                    MessageFactory.text(f"Sorry, I couldn't retrieve your profile information. Error: {str(e)}")
                )
        else:
            await step_context.context.send_activity(
                MessageFactory.text("Authentication failed. Unable to get your profile.")
            )
        
        # End the dialog
        return await step_context.end_dialog()