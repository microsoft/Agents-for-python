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
