from .agents_model import AgentsModel
from .token_response import TokenResponse
from .sign_in_resource import SignInResource

class TokenOrSignInResourceResponse(AgentsModel):
    token_response: TokenResponse = None
    sign_in_resource: SignInResource = None
    