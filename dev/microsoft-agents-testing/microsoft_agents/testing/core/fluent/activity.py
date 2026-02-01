# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Activity-specific fluent utilities (currently commented out).

This module contains specialized assertion classes for Activity objects.
The ActivityExpect class is commented out pending finalization.
"""

from __future__ import annotations

from microsoft_agents.activity import Activity

from typing import Iterable, Self

from microsoft_agents.activity import Activity, ActivityTypes  # TODO: Duplicate import of Activity

from .expect import Expect
from .model_template import ModelTemplate

# TODO: ActivityExpect is commented out - determine if it should be removed or completed

# class ActivityExpect(Expect):
#     """
#     Specialized Expect class for asserting on Activity objects.
    
#     Provides convenience methods for common Activity assertions.

#     Usage:
#         # Assert all activities are messages
#         ActivityExpect(responses).are_messages()

#         # Assert conversation was started
#         ActivityExpect(responses).starts_conversation()

#         # Assert text contains value
#         ActivityExpect(responses).has_text_containing("hello")
#     """

#     def __init__(self, items: Iterable[Activity]) -> None:
#         """Initialize ActivityExpect with Activity objects.
        
#         :param items: An iterable of Activity instances.
#         """
#         super().__init__(items)

#     # =========================================================================
#     # Type Assertions
#     # =========================================================================

#     def are_messages(self) -> Self:
#         """Assert that all activities are of type 'message'.
        
#         :raises AssertionError: If any activity is not a message.
#         :return: Self for chaining.
#         """
#         return self.that(type=ActivityTypes.message)

#     def are_typing(self) -> Self:
#         """Assert that all activities are of type 'typing'.
        
#         :raises AssertionError: If any activity is not typing.
#         :return: Self for chaining.
#         """
#         return self.that(type=ActivityTypes.typing)

#     def are_events(self) -> Self:
#         """Assert that all activities are of type 'event'.
        
#         :raises AssertionError: If any activity is not an event.
#         :return: Self for chaining.
#         """
#         return self.that(type=ActivityTypes.event)

#     def has_type(self, activity_type: str) -> Self:
#         """Assert that all activities have the specified type.
        
#         :param activity_type: The expected activity type.
#         :raises AssertionError: If any activity doesn't match the type.
#         :return: Self for chaining.
#         """
#         return self.that(type=activity_type)

#     def has_any_type(self, activity_type: str) -> Self:
#         """Assert that at least one activity has the specified type.
        
#         :param activity_type: The expected activity type.
#         :raises AssertionError: If no activity matches the type.
#         :return: Self for chaining.
#         """
#         return self.that_for_any(type=activity_type)

#     # =========================================================================
#     # Conversation Flow Assertions
#     # =========================================================================

#     def starts_conversation(self) -> Self:
#         """Assert that the activities include a conversation start.
        
#         Checks for conversationUpdate with membersAdded.
        
#         :raises AssertionError: If no conversation start activity found.
#         :return: Self for chaining.
#         """
#         def is_conversation_start(activity: Activity) -> bool:
#             if activity.type != ActivityTypes.conversation_update:
#                 return False
#             return bool(activity.members_added and len(activity.members_added) > 0)
        
#         return self.that_for_any(is_conversation_start)

#     def ends_conversation(self) -> Self:
#         """Assert that the activities include a conversation end.
        
#         Checks for endOfConversation activity type.
        
#         :raises AssertionError: If no conversation end activity found.
#         :return: Self for chaining.
#         """
#         return self.that_for_any(type=ActivityTypes.end_of_conversation)

#     def has_members_added(self) -> Self:
#         """Assert that at least one activity has members added.
        
#         :raises AssertionError: If no activity has members added.
#         :return: Self for chaining.
#         """
#         def has_members(activity: Activity) -> bool:
#             return bool(activity.members_added and len(activity.members_added) > 0)
        
#         return self.that_for_any(has_members)

#     def has_members_removed(self) -> Self:
#         """Assert that at least one activity has members removed.
        
#         :raises AssertionError: If no activity has members removed.
#         :return: Self for chaining.
#         """
#         def has_removed(activity: Activity) -> bool:
#             return bool(activity.members_removed and len(activity.members_removed) > 0)
        
#         return self.that_for_any(has_removed)

#     # =========================================================================
#     # Text Assertions
#     # =========================================================================

#     def has_text(self, text: str) -> Self:
#         """Assert that all activities have the exact text.
        
#         :param text: The expected text.
#         :raises AssertionError: If any activity doesn't have the exact text.
#         :return: Self for chaining.
#         """
#         return self.that(text=text)

#     def has_any_text(self, text: str) -> Self:
#         """Assert that at least one activity has the exact text.
        
#         :param text: The expected text.
#         :raises AssertionError: If no activity has the exact text.
#         :return: Self for chaining.
#         """
#         return self.that_for_any(text=text)

#     def has_text_containing(self, substring: str) -> Self:
#         """Assert that all activities have text containing the substring.
        
#         :param substring: The substring to search for.
#         :raises AssertionError: If any activity doesn't contain the substring.
#         :return: Self for chaining.
#         """
#         def contains_text(activity: Activity) -> bool:
#             return activity.text is not None and substring in activity.text
        
#         return self.that(contains_text)

#     def has_any_text_containing(self, substring: str) -> Self:
#         """Assert that at least one activity has text containing the substring.
        
#         :param substring: The substring to search for.
#         :raises AssertionError: If no activity contains the substring.
#         :return: Self for chaining.
#         """
#         def contains_text(activity: Activity) -> bool:
#             return activity.text is not None and substring in activity.text
        
#         return self.that_for_any(contains_text)

#     def has_text_matching(self, pattern: str) -> Self:
#         """Assert that all activities have text matching the regex pattern.
        
#         :param pattern: The regex pattern to match.
#         :raises AssertionError: If any activity doesn't match the pattern.
#         :return: Self for chaining.
#         """
#         import re
#         regex = re.compile(pattern)
        
#         def matches_pattern(activity: Activity) -> bool:
#             return activity.text is not None and regex.search(activity.text) is not None
        
#         return self.that(matches_pattern)

#     def has_any_text_matching(self, pattern: str) -> Self:
#         """Assert that at least one activity has text matching the regex pattern.
        
#         :param pattern: The regex pattern to match.
#         :raises AssertionError: If no activity matches the pattern.
#         :return: Self for chaining.
#         """
#         import re
#         regex = re.compile(pattern)
        
#         def matches_pattern(activity: Activity) -> bool:
#             return activity.text is not None and regex.search(activity.text) is not None
        
#         return self.that_for_any(matches_pattern)

#     # =========================================================================
#     # Attachment Assertions
#     # =========================================================================

#     def has_attachments(self) -> Self:
#         """Assert that all activities have at least one attachment.
        
#         :raises AssertionError: If any activity has no attachments.
#         :return: Self for chaining.
#         """
#         def has_attach(activity: Activity) -> bool:
#             return bool(activity.attachments and len(activity.attachments) > 0)
        
#         return self.that(has_attach)

#     def has_any_attachments(self) -> Self:
#         """Assert that at least one activity has attachments.
        
#         :raises AssertionError: If no activity has attachments.
#         :return: Self for chaining.
#         """
#         def has_attach(activity: Activity) -> bool:
#             return bool(activity.attachments and len(activity.attachments) > 0)
        
#         return self.that_for_any(has_attach)

#     def has_attachment_of_type(self, content_type: str) -> Self:
#         """Assert that at least one activity has an attachment of the specified type.
        
#         :param content_type: The attachment content type (e.g., 'image/png').
#         :raises AssertionError: If no matching attachment found.
#         :return: Self for chaining.
#         """
#         def has_type(activity: Activity) -> bool:
#             if not activity.attachments:
#                 return False
#             return any(a.content_type == content_type for a in activity.attachments)
        
#         return self.that_for_any(has_type)

#     def has_adaptive_card(self) -> Self:
#         """Assert that at least one activity has an Adaptive Card attachment.
        
#         :raises AssertionError: If no Adaptive Card found.
#         :return: Self for chaining.
#         """
#         return self.has_attachment_of_type("application/vnd.microsoft.card.adaptive")

#     def has_hero_card(self) -> Self:
#         """Assert that at least one activity has a Hero Card attachment.
        
#         :raises AssertionError: If no Hero Card found.
#         :return: Self for chaining.
#         """
#         return self.has_attachment_of_type("application/vnd.microsoft.card.hero")

#     def has_thumbnail_card(self) -> Self:
#         """Assert that at least one activity has a Thumbnail Card attachment.
        
#         :raises AssertionError: If no Thumbnail Card found.
#         :return: Self for chaining.
#         """
#         return self.has_attachment_of_type("application/vnd.microsoft.card.thumbnail")

#     # =========================================================================
#     # Suggested Actions Assertions
#     # =========================================================================

#     def has_suggested_actions(self) -> Self:
#         """Assert that at least one activity has suggested actions.
        
#         :raises AssertionError: If no activity has suggested actions.
#         :return: Self for chaining.
#         """
#         def has_actions(activity: Activity) -> bool:
#             return bool(
#                 activity.suggested_actions 
#                 and activity.suggested_actions.actions 
#                 and len(activity.suggested_actions.actions) > 0
#             )
        
#         return self.that_for_any(has_actions)

#     def has_suggested_action_titled(self, title: str) -> Self:
#         """Assert that at least one activity has a suggested action with the given title.
        
#         :param title: The expected action title.
#         :raises AssertionError: If no matching suggested action found.
#         :return: Self for chaining.
#         """
#         def has_action_title(activity: Activity) -> bool:
#             if not activity.suggested_actions or not activity.suggested_actions.actions:
#                 return False
#             return any(a.title == title for a in activity.suggested_actions.actions)
        
#         return self.that_for_any(has_action_title)

#     # =========================================================================
#     # Channel/Conversation Assertions
#     # =========================================================================

#     def from_channel(self, channel_id: str) -> Self:
#         """Assert that all activities are from the specified channel.
        
#         :param channel_id: The expected channel ID.
#         :raises AssertionError: If any activity is from a different channel.
#         :return: Self for chaining.
#         """
#         return self.that(channel_id=channel_id)

#     def in_conversation(self, conversation_id: str) -> Self:
#         """Assert that all activities are in the specified conversation.
        
#         :param conversation_id: The expected conversation ID.
#         :raises AssertionError: If any activity is in a different conversation.
#         :return: Self for chaining.
#         """
#         def in_conv(activity: Activity) -> bool:
#             return activity.conversation is not None and activity.conversation.id == conversation_id
        
#         return self.that(in_conv)

#     def from_user(self, user_id: str) -> Self:
#         """Assert that all activities are from the specified user.
        
#         :param user_id: The expected user ID.
#         :raises AssertionError: If any activity is from a different user.
#         :return: Self for chaining.
#         """
#         def from_usr(activity: Activity) -> bool:
#             return activity.from_property is not None and activity.from_property.id == user_id
        
#         return self.that(from_usr)

#     def to_recipient(self, recipient_id: str) -> Self:
#         """Assert that all activities are addressed to the specified recipient.
        
#         :param recipient_id: The expected recipient ID.
#         :raises AssertionError: If any activity is to a different recipient.
#         :return: Self for chaining.
#         """
#         def to_recip(activity: Activity) -> bool:
#             return activity.recipient is not None and activity.recipient.id == recipient_id
        
#         return self.that(to_recip)

#     # =========================================================================
#     # Value/Entity Assertions
#     # =========================================================================

#     def has_value(self) -> Self:
#         """Assert that all activities have a value set.
        
#         :raises AssertionError: If any activity has no value.
#         :return: Self for chaining.
#         """
#         def has_val(activity: Activity) -> bool:
#             return activity.value is not None
        
#         return self.that(has_val)

#     def has_entities(self) -> Self:
#         """Assert that at least one activity has entities.
        
#         :raises AssertionError: If no activity has entities.
#         :return: Self for chaining.
#         """
#         def has_ent(activity: Activity) -> bool:
#             return bool(activity.entities and len(activity.entities) > 0)
        
#         return self.that_for_any(has_ent)

#     def has_semantic_action(self) -> Self:
#         """Assert that at least one activity has a semantic action.
        
#         :raises AssertionError: If no activity has a semantic action.
#         :return: Self for chaining.
#         """
#         def has_action(activity: Activity) -> bool:
#             return activity.semantic_action is not None
        
#         return self.that_for_any(has_action)