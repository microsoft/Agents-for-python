from microsoft_agents.activity import (
    TokenExchangeState
)

def mock_class_TokenExchangeState(self, mocker, get_encoded_value_return):
    mocker.patch.object(
        TokenExchangeState, "get_encoded_state", return_value=get_encoded_value_return
    )