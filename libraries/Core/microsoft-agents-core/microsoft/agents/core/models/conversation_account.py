from typing import Optional
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ConversationAccount(AgentsModel):
    """Conversation account represents the identity of the conversation within a channel.

    :param is_group: Indicates whether the conversation contains more than two
     participants at the time the activity was generated
    :type is_group: bool
    :param conversation_type: Indicates the type of the conversation in
     channels that distinguish between conversation types
    :type conversation_type: str
    :param id: Channel id for the user or agent on this channel (Example:
     joe@smith.com, or @joesmith or 123456)
    :type id: str
    :param name: Display friendly name
    :type name: str
    :param aad_object_id: This account's object ID within Azure Active
     Directory (AAD)
    :type aad_object_id: str
    :param role: Role of the entity behind the account
    :type role: str or ~microsoft.agents.protocols.models.RoleTypes
    :param tenant_id: This conversation's tenant ID
    :type tenant_id: str
    :param properties: This conversation's properties
    :type properties: object
    """

    is_group: bool = None
    conversation_type: NonEmptyString = None
    id: NonEmptyString
    name: NonEmptyString = None
    aad_object_id: NonEmptyString = None
    role: NonEmptyString = None
    tenant_id: Optional[NonEmptyString] = None
    properties: object = None
