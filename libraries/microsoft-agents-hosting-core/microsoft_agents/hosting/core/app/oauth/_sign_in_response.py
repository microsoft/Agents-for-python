# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


from typing import Optional

from microsoft_agents.activity import TokenResponse

from ..._oauth import _FlowStateTag


class _SignInResponse:
    """Response for a sign-in attempt, including the token response and flow state tag."""

    token_response: TokenResponse
    tag: _FlowStateTag

    def __init__(
        self,
        token_response: Optional[TokenResponse] = None,
        tag: _FlowStateTag = _FlowStateTag.FAILURE,
    ) -> None:
        self.token_response = token_response or TokenResponse()
        self.tag = tag

    def sign_in_complete(self) -> bool:
        """Return True if the sign-in flow is complete (either successful or no attempt needed)."""
        return self.tag in [_FlowStateTag.COMPLETE, _FlowStateTag.NOT_STARTED]
