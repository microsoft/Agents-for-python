from typing import Optional

from microsoft_agents.activity import TokenResponse

from ...oauth import FlowStateTag


class SignInResponse:
    """Response for a sign-in attempt, including the token response and flow state tag."""

    token_response: TokenResponse
    tag: FlowStateTag

    def __init__(
        self,
        token_response: Optional[TokenResponse] = None,
        tag: FlowStateTag = FlowStateTag.FAILURE,
    ) -> None:
        self.token_response = token_response or TokenResponse()
        self.tag = tag

    def sign_in_complete(self) -> bool:
        """Return True if the sign-in flow is complete (either successful or no attempt needed)."""
        return self.tag in [FlowStateTag.COMPLETE, FlowStateTag.NOT_STARTED]
