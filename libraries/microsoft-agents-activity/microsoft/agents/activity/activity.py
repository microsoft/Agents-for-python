from copy import copy
from datetime import datetime, timezone
from typing import Optional
from pydantic import Field, SerializeAsAny
from .activity_types import ActivityTypes
from .channel_account import ChannelAccount
from .conversation_account import ConversationAccount
from .mention import Mention
from .message_reaction import MessageReaction
from .resource_response import ResourceResponse
from .suggested_actions import SuggestedActions
from .attachment import Attachment
from .entity import Entity
from .conversation_reference import ConversationReference
from .text_highlight import TextHighlight
from .semantic_action import SemanticAction
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


# TODO: A2A Agent 2 is responding with None as id, had to mark it as optional (investigate)
class Activity(AgentsModel):
    """An Activity is the basic communication type for the protocol.

    :param type: Contains the activity type. Possible values include:
        'message', 'contactRelationUpdate', 'conversationUpdate', 'typing',
        'endOfConversation', 'event', 'invoke', 'deleteUserData', 'messageUpdate',
        'messageDelete', 'installationUpdate', 'messageReaction', 'suggestion',
        'trace', 'handoff'
    :type type: str or ~microsoft.agents.protocols.models.ActivityTypes
    :param id: Contains an ID that uniquely identifies the activity on the channel.
    :type id: str
    :param timestamp: Contains the date and time that the message was sent, in UTC, expressed in ISO-8601 format.
    :type timestamp: datetime
    :param local_timestamp: Contains the local date and time of the message expressed in ISO-8601 format.
        For example, 2016-09-23T13:07:49.4714686-07:00.
    :type local_timestamp: datetime
    :param local_timezone: Contains the name of the local timezone of the message, expressed in IANA Time Zone database format.
        For example, America/Los_Angeles.
    :type local_timezone: str
    :param service_url: Contains the URL that specifies the channel's service endpoint. Set by the channel.
    :type service_url: str
    :param channel_id: Contains an ID that uniquely identifies the channel. Set by the channel.
    :type channel_id: str
    :param from_property: Identifies the sender of the message.
    :type from_property: ~microsoft.agents.protocols.models.ChannelAccount
    :param conversation: Identifies the conversation to which the activity belongs.
    :type conversation: ~microsoft.agents.protocols.models.ConversationAccount
    :param recipient: Identifies the recipient of the message.
    :type recipient: ~microsoft.agents.protocols.models.ChannelAccount
    :param text_format: Format of text fields Default:markdown. Possible values include: 'markdown', 'plain', 'xml'
    :type text_format: str or ~microsoft.agents.protocols.models.TextFormatTypes
    :param attachment_layout: The layout hint for multiple attachments. Default: list. Possible values include: 'list', 'carousel'
    :type attachment_layout: str or ~microsoft.agents.protocols.models.AttachmentLayoutTypes
    :param members_added: The collection of members added to the conversation.
    :type members_added: list[~microsoft.agents.protocols.models.ChannelAccount]
    :param members_removed: The collection of members removed from the conversation.
    :type members_removed: list[~microsoft.agents.protocols.models.ChannelAccount]
    :param reactions_added: The collection of reactions added to the conversation.
    :type reactions_added: list[~microsoft.agents.protocols.models.MessageReaction]
    :param reactions_removed: The collection of reactions removed from the conversation.
    :type reactions_removed: list[~microsoft.agents.protocols.models.MessageReaction]
    :param topic_name: The updated topic name of the conversation.
    :type topic_name: str
    :param history_disclosed: Indicates whether the prior history of the channel is disclosed.
    :type history_disclosed: bool
    :param locale: A locale name for the contents of the text field. The locale name is a combination of an ISO 639 two- or three-letter
        culture code associated with a language and an ISO 3166 two-letter subculture code associated with a country or region.
        The locale name can also correspond to a valid BCP-47 language tag.
    :type locale: str
    :param text: The text content of the message.
    :type text: str
    :param speak: The text to speak.
    :type speak: str
    :param input_hint: Indicates whether your agent is accepting, expecting, or ignoring user input after the message is delivered to the client.
        Possible values include: 'acceptingInput', 'ignoringInput', 'expectingInput'
    :type input_hint: str or ~microsoft.agents.protocols.models.InputHints
    :param summary: The text to display if the channel cannot render cards.
    :type summary: str
    :param suggested_actions: The suggested actions for the activity.
    :type suggested_actions: ~microsoft.agents.protocols.models.SuggestedActions
    :param attachments: Attachments
    :type attachments: list[~microsoft.agents.protocols.models.Attachment]
    :param entities: Represents the entities that were mentioned in the message.
    :type entities: list[~microsoft.agents.protocols.models.Entity]
    :param channel_data: Contains channel-specific content.
    :type channel_data: object
    :param action: Indicates whether the recipient of a contactRelationUpdate was added or removed from the sender's contact list.
    :type action: str
    :param reply_to_id: Contains the ID of the message to which this message is a reply.
    :type reply_to_id: str
    :param label: A descriptive label for the activity.
    :type label: str
    :param value_type: The type of the activity's value object.
    :type value_type: str
    :param value: A value that is associated with the activity.
    :type value: object
    :param name: The name of the operation associated with an invoke or event activity.
    :type name: str
    :param relates_to: A reference to another conversation or activity.
    :type relates_to: ~microsoft.agents.protocols.models.ConversationReference
    :param code: The a code for endOfConversation activities that indicates why the conversation ended. Possible values include: 'unknown',
        'completedSuccessfully', 'userCancelled', 'botTimedOut', 'botIssuedInvalidMessage', 'channelFailed'
    :type code: str or ~microsoft.agents.protocols.models.EndOfConversationCodes
    :param expiration: The time at which the activity should be considered to be "expired" and should not be presented to the recipient.
    :type expiration: datetime
    :param importance: The importance of the activity. Possible values include: 'low', 'normal', 'high'
    :type importance: str or ~microsoft.agents.protocols.models.ActivityImportance
    :param delivery_mode: A delivery hint to signal to the recipient alternate delivery paths for the activity.
        The default delivery mode is "default". Possible values include: 'normal', 'notification', 'expectReplies', 'ephemeral'
    :type delivery_mode: str or ~microsoft.agents.protocols.models.DeliveryModes
    :param listen_for: List of phrases and references that speech and language priming systems should listen for
    :type listen_for: list[str]
    :param text_highlights: The collection of text fragments to highlight when the activity contains a ReplyToId value.
    :type text_highlights: list[~microsoft.agents.protocols.models.TextHighlight]
    :param semantic_action: An optional programmatic action accompanying this request
    :type semantic_action: ~microsoft.agents.protocols.models.SemanticAction
    :param caller_id: A string containing an IRI identifying the caller of an agent. This field is not intended to be transmitted over the wire,
        but is instead populated by agents and clients based on cryptographically verifiable data that asserts the identity of the callers (e.g. tokens).
    :type caller_id: str
    """

    type: NonEmptyString
    id: Optional[NonEmptyString] = None
    timestamp: datetime = None
    local_timestamp: datetime = None
    local_timezone: NonEmptyString = None
    service_url: NonEmptyString = None
    channel_id: NonEmptyString = None
    from_property: ChannelAccount = Field(None, alias="from")
    conversation: ConversationAccount = None
    recipient: ChannelAccount = None
    text_format: NonEmptyString = None
    attachment_layout: NonEmptyString = None
    members_added: list[ChannelAccount] = None
    members_removed: list[ChannelAccount] = None
    reactions_added: list[MessageReaction] = None
    reactions_removed: list[MessageReaction] = None
    topic_name: NonEmptyString = None
    history_disclosed: bool = None
    locale: NonEmptyString = None
    text: str = None
    speak: str = None
    input_hint: NonEmptyString = None
    summary: NonEmptyString = None
    suggested_actions: SuggestedActions = None
    attachments: list[Attachment] = None
    entities: list[SerializeAsAny[Entity]] = None
    channel_data: object = None
    action: NonEmptyString = None
    reply_to_id: NonEmptyString = None
    label: NonEmptyString = None
    value_type: NonEmptyString = None
    value: object = None
    name: NonEmptyString = None
    relates_to: ConversationReference = None
    code: NonEmptyString = None
    expiration: datetime = None
    importance: NonEmptyString = None
    delivery_mode: NonEmptyString = None
    listen_for: list[NonEmptyString] = None
    text_highlights: list[TextHighlight] = None
    semantic_action: SemanticAction = None
    caller_id: NonEmptyString = None

    def apply_conversation_reference(
        self, reference: ConversationReference, is_incoming: bool = False
    ):
        """
        Updates this activity with the delivery information from an existing ConversationReference.

        :param reference: The existing conversation reference.
        :param is_incoming: Optional, True to treat the activity as an incoming activity, where the agent is the recipient; otherwise, False.
            Default is False, and the activity will show the agent as the sender.

        :returns: This activity, updated with the delivery information.

        .. remarks::
            Call GetConversationReference on an incoming activity to get a conversation reference that you can then use to update an
            outgoing activity with the correct delivery information.
        """
        self.channel_id = reference.channel_id
        self.service_url = reference.service_url
        self.conversation = reference.conversation

        if reference.locale is not None:
            self.locale = reference.locale

        if is_incoming:
            self.from_property = reference.user
            self.recipient = reference.agent

            if reference.activity_id is not None:
                self.id = reference.activity_id
        else:
            self.from_property = reference.agent
            self.recipient = reference.user

            if reference.activity_id is not None:
                self.reply_to_id = reference.activity_id

        return self

    def as_contact_relation_update_activity(self):
        """
        Returns this activity as a ContactRelationUpdateActivity object; or None, if this is not that type of activity.

        :returns: This activity as a message activity; or None.
        """
        return (
            self if self.__is_activity(ActivityTypes.contact_relation_update) else None
        )

    def as_conversation_update_activity(self):
        """
        Returns this activity as a ConversationUpdateActivity object; or None, if this is not that type of activity.

        :returns: This activity as a conversation update activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.conversation_update) else None

    def as_end_of_conversation_activity(self):
        """
        Returns this activity as an EndOfConversationActivity object; or None, if this is not that type of activity.

        :returns: This activity as an end of conversation activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.end_of_conversation) else None

    def as_event_activity(self):
        """
        Returns this activity as an EventActivity object; or None, if this is not that type of activity.

        :returns: This activity as an event activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.event) else None

    def as_handoff_activity(self):
        """
        Returns this activity as a HandoffActivity object; or None, if this is not that type of activity.

        :returns: This activity as a handoff activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.handoff) else None

    def as_installation_update_activity(self):
        """
        Returns this activity as an InstallationUpdateActivity object; or None, if this is not that type of activity.

        :returns: This activity as an installation update activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.installation_update) else None

    def as_invoke_activity(self):
        """
        Returns this activity as an InvokeActivity object; or None, if this is not that type of activity.

        :returns: This activity as an invoke activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.invoke) else None

    def as_message_activity(self):
        """
        Returns this activity as a MessageActivity object; or None, if this is not that type of activity.

        :returns: This activity as a message activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.message) else None

    def as_message_delete_activity(self):
        """
        Returns this activity as a MessageDeleteActivity object; or None, if this is not that type of activity.

        :returns: This activity as a message delete request; or None.
        """
        return self if self.__is_activity(ActivityTypes.message_delete) else None

    def as_message_reaction_activity(self):
        """
        Returns this activity as a MessageReactionActivity object; or None, if this is not that type of activity.

        :return: This activity as a message reaction activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.message_reaction) else None

    def as_message_update_activity(self):
        """
        Returns this activity as an MessageUpdateActivity object; or None, if this is not that type of activity.

        :returns: This activity as a message update request; or None.
        """
        return self if self.__is_activity(ActivityTypes.message_update) else None

    def as_suggestion_activity(self):
        """
        Returns this activity as a SuggestionActivity object; or None, if this is not that type of activity.

        :returns: This activity as a suggestion activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.suggestion) else None

    def as_trace_activity(self):
        """
        Returns this activity as a TraceActivity object; or None, if this is not that type of activity.

        :returns: This activity as a trace activity; or None.
        """
        return self if self.__is_activity(ActivityTypes.trace) else None

    def as_typing_activity(self):
        """
        Returns this activity as a TypingActivity object; or null, if this is not that type of activity.

        :returns: This activity as a typing activity; or null.
        """
        return self if self.__is_activity(ActivityTypes.typing) else None

    @staticmethod
    def create_contact_relation_update_activity():
        """
        Creates an instance of the :class:`Activity` class as a ContactRelationUpdateActivity object.

        :returns: The new contact relation update activity.
        """
        return Activity(type=ActivityTypes.contact_relation_update)

    @staticmethod
    def create_conversation_update_activity():
        """
        Creates an instance of the :class:`Activity` class as a ConversationUpdateActivity object.

        :returns: The new conversation update activity.
        """
        return Activity(type=ActivityTypes.conversation_update)

    @staticmethod
    def create_end_of_conversation_activity():
        """
        Creates an instance of the :class:`Activity` class as an EndOfConversationActivity object.

        :returns: The new end of conversation activity.
        """
        return Activity(type=ActivityTypes.end_of_conversation)

    @staticmethod
    def create_event_activity():
        """
        Creates an instance of the :class:`Activity` class as an EventActivity object.

        :returns: The new event activity.
        """
        return Activity(type=ActivityTypes.event)

    @staticmethod
    def create_handoff_activity():
        """
        Creates an instance of the :class:`Activity` class as a HandoffActivity object.

        :returns: The new handoff activity.
        """
        return Activity(type=ActivityTypes.handoff)

    @staticmethod
    def create_invoke_activity():
        """
        Creates an instance of the :class:`Activity` class as an InvokeActivity object.

        :returns: The new invoke activity.
        """
        return Activity(type=ActivityTypes.invoke)

    @staticmethod
    def create_message_activity():
        """
        Creates an instance of the :class:`Activity` class as a MessageActivity object.

        :returns: The new message activity.
        """
        return Activity(type=ActivityTypes.message)

    def create_reply(self, text: str = None, locale: str = None):
        """
        Creates a new message activity as a response to this activity.

        :param text: The text of the reply.
        :param locale: The language code for the text.

        :returns: The new message activity.

        .. remarks::
            The new activity sets up routing information based on this activity.
        """
        return Activity(
            type=ActivityTypes.message,
            timestamp=datetime.now(timezone.utc),
            from_property=ChannelAccount(
                id=self.recipient.id if self.recipient else None,
                name=self.recipient.name if self.recipient else None,
            ),
            recipient=ChannelAccount(
                id=self.from_property.id if self.from_property else None,
                name=self.from_property.name if self.from_property else None,
            ),
            reply_to_id=(
                self.id
                if type != ActivityTypes.conversation_update
                or self.channel_id not in ["directline", "webchat"]
                else None
            ),
            service_url=self.service_url,
            channel_id=self.channel_id,
            conversation=ConversationAccount(
                is_group=self.conversation.is_group,
                id=self.conversation.id,
                name=self.conversation.name,
            ),
            text=text if text else "",
            locale=locale if locale else self.locale,
            attachments=[],
            entities=[],
        )

    def create_trace(
        self, name: str, value: object = None, value_type: str = None, label: str = None
    ):
        """
        Creates a new trace activity based on this activity.

        :param name: The name of the trace operation to create.
        :param value: Optional, the content for this trace operation.
        :param value_type: Optional, identifier for the format of the value. Default is the name of type of the value.
        :param label: Optional, a descriptive label for this trace operation.

        :returns: The new trace activity.
        """
        if not value_type and value:
            value_type = type(value)

        return Activity(
            type=ActivityTypes.trace,
            timestamp=datetime.now(timezone.utc),
            from_property=ChannelAccount(
                id=self.recipient.id if self.recipient else None,
                name=self.recipient.name if self.recipient else None,
            ),
            recipient=ChannelAccount(
                id=self.from_property.id if self.from_property else None,
                name=self.from_property.name if self.from_property else None,
            ),
            reply_to_id=(
                self.id
                if type != ActivityTypes.conversation_update
                or self.channel_id not in ["directline", "webchat"]
                else None
            ),
            service_url=self.service_url,
            channel_id=self.channel_id,
            conversation=ConversationAccount(
                is_group=self.conversation.is_group,
                id=self.conversation.id,
                name=self.conversation.name,
            ),
            name=name,
            label=label,
            value_type=value_type,
            value=value,
        ).as_trace_activity()

    @staticmethod
    def create_trace_activity(
        name: str, value: object = None, value_type: str = None, label: str = None
    ):
        """
        Creates an instance of the :class:`Activity` class as a TraceActivity object.

        :param name: The name of the trace operation to create.
        :param value: Optional, the content for this trace operation.
        :param value_type: Optional, identifier for the format of the value. Default is the name of type of the value.
        :param label: Optional, a descriptive label for this trace operation.

        :returns: The new trace activity.
        """
        if not value_type and value:
            value_type = type(value)

        return Activity(
            type=ActivityTypes.trace,
            name=name,
            label=label,
            value_type=value_type,
            value=value,
        )

    @staticmethod
    def create_typing_activity() -> "Activity":
        """
        Creates an instance of the :class:`Activity` class as a TypingActivity object.

        :returns: The new typing activity.
        """
        return Activity(type=ActivityTypes.typing)

    def get_conversation_reference(self) -> ConversationReference:
        """
        Creates a ConversationReference based on this activity.

        :returns: A conversation reference for the conversation that contains this activity.
        """

        return ConversationReference(
            activity_id=(
                self.id
                if self.type != ActivityTypes.conversation_update
                or self.channel_id not in ["directline", "webchat"]
                else None
            ),
            user=copy(self.from_property),
            agent=copy(self.recipient),
            conversation=copy(self.conversation),
            channel_id=self.channel_id,
            locale=self.locale,
            service_url=self.service_url,
        )

    def get_mentions(self) -> list[Mention]:
        """
        Resolves the mentions from the entities of this activity.

        :returns: The array of mentions; or an empty array, if none are found.

        .. remarks::
            This method is defined on the :class:`Activity` class, but is only intended for use with a message activity,
            where the activity Activity.Type is set to ActivityTypes.Message.
        """
        _list = self.entities
        return [x for x in _list if str(x.type).lower() == "mention"]

    def get_reply_conversation_reference(
        self, reply: ResourceResponse
    ) -> ConversationReference:
        """
        Create a ConversationReference based on this Activity's Conversation info and the ResourceResponse from sending an activity.

        :param reply: ResourceResponse returned from send_activity.

        :return: A ConversationReference that can be stored and used later to delete or update the activity.
        """
        reference = self.get_conversation_reference()
        reference.activity_id = reply.id
        return reference

    def has_content(self) -> bool:
        """
        Indicates whether this activity has content.

        :returns: True, if this activity has any content to send; otherwise, false.

        .. remarks::
            This method is defined on the :class:`Activity` class, but is only intended for use with a message activity,
            where the activity Activity.Type is set to ActivityTypes.Message.
        """
        if self.text and self.text.strip():
            return True

        if self.summary and self.summary.strip():
            return True

        if self.attachments and len(self.attachments) > 0:
            return True

        if self.channel_data:
            return True

        return False

    def is_from_streaming_connection(self) -> bool:
        """
        Determine if the Activity was sent via an Http/Https connection or Streaming.
        This can be determined by looking at the service_url property:
        (1) All channels that send messages via http/https are not streaming.
        (2) Channels that send messages via streaming have a ServiceUrl that does not begin with http/https.

        :returns: True if the Activity originated from a streaming connection.
        """
        if self.service_url:
            return not self.service_url.lower().startswith("http")
        return False

    def __is_activity(self, activity_type: str) -> bool:
        """
        Indicates whether this activity is of a specified activity type.

        :param activity_type: The activity type to check for.
        :return: True if this activity is of the specified activity type; otherwise, False.
        """
        if self.type is None:
            return False

        type_attribute = str(self.type).lower()
        activity_type = str(activity_type).lower()

        result = type_attribute.startswith(activity_type)

        if result:
            result = len(type_attribute) == len(activity_type)

            if not result:
                result = (
                    len(type_attribute) > len(activity_type)
                    and type_attribute[len(activity_type)] == "/"
                )

        return result
