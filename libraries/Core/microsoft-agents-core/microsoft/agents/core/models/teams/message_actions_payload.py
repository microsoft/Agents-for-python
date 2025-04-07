# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Annotated, List

from .message_actions_payload_from import MessageActionsPayloadFrom
from .message_actions_payload_body import MessageActionsPayloadBody
from .message_actions_payload_attachment import MessageActionsPayloadAttachment
from .message_actions_payload_mention import MessageActionsPayloadMention
from .message_actions_payload_reaction import MessageActionsPayloadReaction


class MessageActionsPayload(AgentsModel):
    """Represents the individual message within a chat or channel where a message action is taken.

    :param id: Unique id of the message.
    :type id: str
    :param reply_to_id: Id of the parent/root message of the thread.
    :type reply_to_id: str
    :param message_type: Type of message - automatically set to message.
    :type message_type: str
    :param created_date_time: Timestamp of when the message was created.
    :type created_date_time: str
    :param last_modified_date_time: Timestamp of when the message was edited or updated.
    :type last_modified_date_time: str
    :param deleted: Indicates whether a message has been soft deleted.
    :type deleted: bool
    :param subject: Subject line of the message.
    :type subject: str
    :param summary: Summary text of the message that could be used for notifications.
    :type summary: str
    :param importance: The importance of the message. Possible values include: 'normal', 'high', 'urgent'
    :type importance: Annotated[str, Field(pattern=r"^(normal|high|urgent)$")]
    :param locale: Locale of the message set by the client.
    :type locale: str
    :param link_to_message: Link back to the message.
    :type link_to_message: str
    :param from_property: Sender of the message.
    :type from_property: MessageActionsPayloadFrom
    :param body: Plaintext/HTML representation of the content of the message.
    :type body: MessageActionsPayloadBody
    :param attachment_layout: How the attachment(s) are displayed in the message.
    :type attachment_layout: str
    :param attachments: Attachments in the message - card, image, file, etc.
    :type attachments: List[MessageActionsPayloadAttachment]
    :param mentions: List of entities mentioned in the message.
    :type mentions: List[MessageActionsPayloadMention]
    :param reactions: Reactions for the message.
    :type reactions: List[MessageActionsPayloadReaction]
    """

    id: str = None
    reply_to_id: str = None
    message_type: str = None
    created_date_time: str = None
    last_modified_date_time: str = None
    deleted: bool = None
    subject: str = None
    summary: str = None
    importance: Annotated[str, Field(pattern=r"^(normal|high|urgent)$")] = None
    locale: str = None
    link_to_message: str = None
    from_property: MessageActionsPayloadFrom = None
    body: MessageActionsPayloadBody = None
    attachment_layout: str = None
    attachments: List[MessageActionsPayloadAttachment] = None
    mentions: List[MessageActionsPayloadMention] = None
    reactions: List[MessageActionsPayloadReaction] = None
