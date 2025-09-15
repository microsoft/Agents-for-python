from microsoft_agents.activity import AgentsModel

from .messaging_extension_parameter import MessagingExtensionParameter
from .messaging_extension_query_options import MessagingExtensionQueryOptions

class MessagingExtensionQuery(AgentsModel):
    command_id: Optional[str] = None
    parameters: Optional[list[MessagingExtensionParameter]] = None
    query_options: Optional[MessagingExtensionQueryOptions] = None
    state: Optional[str] = None