import email
from token import OP
from typing import Optional

from microsoft_agents.activity import ChannelAccount

class TeamsChannelAccount(ChannelAccount):
    given_name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    user_principal_name: Optional[str] = None
    tenant_id: Optional[str] = None
    user_role: Optional[str] = None