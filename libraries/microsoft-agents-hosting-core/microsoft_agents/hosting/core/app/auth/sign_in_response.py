from typing import Optional

from microsoft_agents.activity import TokenResponse

from ...oauth import FlowStateTag

class SignInResponse:
    token_response: TokenResponse
    tag: FlowStateTag

    def __init__(self, token_response: Optional[TokenResponse] = None, tag: FlowStateTag = FlowStateTag.FAILURE) -> None:
        self.token_response = token_response or TokenResponse()
        self.tag = tag

    def sign_in_complete(self) -> bool:
        return self.tag in [FlowStateTag.COMPLETE, FlowStateTag.NOT_STARTED]