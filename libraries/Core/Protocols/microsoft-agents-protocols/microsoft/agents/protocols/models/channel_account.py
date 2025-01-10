from ._agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ChannelAccount(AgentsModel):
    """Channel account information needed to route a message.

    :param id: Channel id for the user or bot on this channel (Example:
     joe@smith.com, or @joesmith or 123456)
    :type id: str
    :param name: Display friendly name
    :type name: str
    :param aad_object_id: This account's object ID within Azure Active
     Directory (AAD)
    :type aad_object_id: str
    :param role: Role of the entity behind the account (Example: User, Bot,
     etc.). Possible values include: 'user', 'bot'
    :type role: str or ~microsoft.agents.protocols.models.RoleTypes
    """

    id: NonEmptyString
    name: NonEmptyString = None
    aad_object_id: NonEmptyString = None
    role: NonEmptyString = None
    properties: object = None
