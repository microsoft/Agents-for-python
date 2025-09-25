from typing import Optional
from dataclasses import dataclass

from microsoft_agents.activity import TokenResponse

from ...oauth import FlowStateTag

@dataclass
class SignInResponse:
    token_response: TokenResponse = TokenResponse()
    tag: FlowStateTag = FlowStateTag.FAILURE