from pydantic import BaseModel
from typing import List, Optional


class MessageActionsPayload(BaseModel):
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
    :type importance: str
    :param locale: Locale of the message set by the client.
    :type locale: str
    :param link_to_message: Link back to the message.
    :type link_to_message: str
    :param from_property: Sender of the message.
    :type from_property: Optional["MessageActionsPayloadFrom"]
    :param body: Plaintext/HTML representation of the content of the message.
    :type body: Optional["MessageActionsPayloadBody"]
    :param attachment_layout: How the attachment(s) are displayed in the message.
    :type attachment_layout: str
    :param attachments: Attachments in the message - card, image, file, etc.
    :type attachments: List["MessageActionsPayloadAttachment"]
    :param mentions: List of entities mentioned in the message.
    :type mentions: List["MessageActionsPayloadMention"]
    :param reactions: Reactions for the message.
    :type reactions: List["MessageActionsPayloadReaction"]
    """

    id: str
    reply_to_id: str
    message_type: str
    created_date_time: str
    last_modified_date_time: str
    deleted: bool
    subject: str
    summary: str
    importance: str
    locale: str
    link_to_message: str
    from_property: Optional["MessageActionsPayloadFrom"]
    body: Optional["MessageActionsPayloadBody"]
    attachment_layout: str
    attachments: List["MessageActionsPayloadAttachment"]
    mentions: List["MessageActionsPayloadMention"]
    reactions: List["MessageActionsPayloadReaction"]
