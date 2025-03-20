import jwt

from jwt import PyJWKClient, PyJWK, decode, get_unverified_header

from .agent_auth_configuration import AgentAuthConfiguration
from .claims_identity import ClaimsIdentity


class JwtTokenValidator:
    def __init__(self, configuration: AgentAuthConfiguration):
        self.configuration = configuration

    def validate_token(self, token: str) -> ClaimsIdentity:
        key = self._get_public_key_or_secret(token)
        decoded_token = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            leeway=5.0,
            options={"verify_aud": False},
        )
        if decoded_token["aud"] != self.configuration.CLIENT_ID:
            raise ValueError("Invalid audience.")

        # This probably should return a ClaimsIdentity
        return ClaimsIdentity(decoded_token, True)

    def _get_public_key_or_secret(self, token: str) -> PyJWK:
        header = get_unverified_header(token)
        unverified_payload: dict = decode(token, options={"verify_signature": False})

        jwksUri = (
            "https://login.botframework.com/v1/.well-known/keys"
            if unverified_payload.get("iss") == "https://api.botframework.com"
            else f"https://login.microsoftonline.com/{self.configuration.TENANT_ID}/discovery/v2.0/keys"
        )

        jwks_client = PyJWKClient(jwksUri)

        key = jwks_client.get_signing_key(header["kid"])
        return key
