from typing import Union, Literal, Optional, TypeVar

from microsoft_agents.activity import AgentsModel

ApplicationIdentityType = TypeVar("ApplicationIdentityType",
    Literal["aadApplication", "bot", "tenantBot", "office365Connector", "webhook"])

class MessageActionsPayloadApp(AgentsModel):
    application_identity_type: Optional[ApplicationIdentityType] = None
    id: Optional[str] = None
    display_name: Optional[str] = None