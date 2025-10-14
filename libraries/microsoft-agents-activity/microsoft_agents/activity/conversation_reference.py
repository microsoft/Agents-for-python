# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from uuid import uuid4 as uuid
from typing import Optional
import logging

from pydantic import Field

from .channel_account import ChannelAccount
from ._channel_id_field_mixin import _ChannelIdFieldMixin
from .channel_id import ChannelId
from .conversation_account import ConversationAccount
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString
from .activity_types import ActivityTypes
from .activity_event_names import ActivityEventNames

logger = logging.getLogger(__name__)


class ConversationReference(AgentsModel, _ChannelIdFieldMixin):
    """An object relating to a particular point in a conversation.

    :param activity_id: (Optional) ID of the activity to refer to
    :type activity_id: str
    :param user: (Optional) User participating in this conversation
    :type user: ~microsoft_agents.activity.ChannelAccount
    :param agent: Agent participating in this conversation
    :type agent: ~microsoft_agents.activity.ChannelAccount
    :param conversation: Conversation reference
    :type conversation: ~microsoft_agents.activity.ConversationAccount
    :param channel_id: Channel ID
    :type channel_id: ~microsoft_agents.activity.ChannelId
    :param locale: A locale name for the contents of the text field.
        The locale name is a combination of an ISO 639 two- or three-letter
        culture code associated with a language and an ISO 3166 two-letter
        subculture code associated with a country or region.
        The locale name can also correspond to a valid BCP-47 language tag.
    :type locale: str
    :param service_url: Service endpoint where operations concerning the
     referenced conversation may be performed
    :type service_url: str
    """

    # optionals here are due to webchat
    activity_id: Optional[NonEmptyString] = None
    user: Optional[ChannelAccount] = None
    agent: ChannelAccount = Field(None, alias="bot")
    conversation: ConversationAccount
    locale: Optional[NonEmptyString] = None
    service_url: NonEmptyString = None

    def get_continuation_activity(self) -> "Activity":  # type: ignore
        from .activity import Activity

        return Activity(
            type=ActivityTypes.event,
            name=ActivityEventNames.continue_conversation,
            id=str(uuid()),
            channel_id=self.channel_id,
            service_url=self.service_url,
            conversation=self.conversation,
            recipient=self.agent,
            from_property=self.user,
            relates_to=self,
        )
