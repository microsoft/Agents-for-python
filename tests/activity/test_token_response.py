import base64
import json

import pytest
from microsoft_agents.activity import TokenResponse


def test_token_response_model_token_enforcement():
    with pytest.raises(Exception):
        TokenResponse(token="")
    with pytest.raises(Exception):
        TokenResponse(token=None)


@pytest.mark.parametrize(
    "token_response", [TokenResponse(), TokenResponse(expiration="expiration")]
)
def test_token_response_bool_op_false(token_response):
    assert not bool(token_response)


@pytest.mark.parametrize(
    "token_response",
    [TokenResponse(token="token"), TokenResponse(token="a", expiration="a")],
)
def test_token_response_bool_op_true(token_response):
    assert bool(token_response)


def _create_unsigned_jwt(payload: dict) -> str:
    header = {"alg": "none", "typ": "JWT"}

    def encode_segment(value: dict) -> str:
        value_json = json.dumps(value, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(value_json).rstrip(b"=").decode()

    return f"{encode_segment(header)}.{encode_segment(payload)}."


@pytest.mark.parametrize(
    "payload",
    [
        {"aud": "api://test-app-id", "appid": "test-app-id"},
        {"aud": "api://test-app-id", "appid": "test-app-id", "ver": "1.0"},
        {"aud": "api://test-app-id", "azp": "test-app-id", "ver": "2.0"},
    ],
)
def test_token_response_is_exchangeable_true(payload):
    token_response = TokenResponse(token=_create_unsigned_jwt(payload))

    assert token_response.is_exchangeable()


@pytest.mark.parametrize(
    "payload",
    [
        {"aud": "api://test-app-id", "appid": "test-app-id", "idtyp": "user"},
        {"aud": "api://test-app-id"},
        {"appid": "test-app-id"},
        {"aud": "api://test-app-id", "appid": "other-app-id", "ver": "1.0"},
        {"aud": "api://test-app-id", "azp": "other-app-id", "ver": "2.0"},
        {"aud": "api://test-app-id", "appid": "test-app-id", "ver": "3.0"},
    ],
)
def test_token_response_is_exchangeable_false(payload):
    token_response = TokenResponse(token=_create_unsigned_jwt(payload))

    assert not token_response.is_exchangeable()


def test_token_response_is_exchangeable_false_for_invalid_token():
    token_response = TokenResponse(token="not-a-jwt")

    assert not token_response.is_exchangeable()
