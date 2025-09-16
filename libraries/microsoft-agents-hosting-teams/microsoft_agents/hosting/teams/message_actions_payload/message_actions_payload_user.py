from typing import TypeVar, Literal, Optional

from microsoft_agents.activity import AgentsModel

UserIdentityType = TypeVar("UserIdentityType", Literal["aadUser", "onPremiseAadUser", "anonymousGuest", "federatedUser"])

class MessageActionsPayloadUser(AgentsModel):
    user_identity_type: Optional[UserIdentityType] = None
    id: Optional[str] = None
    display_name: Optional[str] = None