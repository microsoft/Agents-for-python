# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from .token_response import TokenResponse
from .sign_in_resource import SignInResource


class TokenOrSignInResourceResponse(AgentsModel):
    """Represents the response containing either a token or a sign-in resource.

    One of the two properties should be set (if returned from the 'getTokenOrSignInResource' endpoint), not both.

    :param token_response: The token response.
    :type token_response: TokenResponse
    :param sign_in_resource: The sign-in resource.
    :type sign_in_resource: SignInResource
    """

    token_response: TokenResponse = None
    sign_in_resource: SignInResource = None
