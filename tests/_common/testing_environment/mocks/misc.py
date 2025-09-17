from microsoft_agents.activity import (
    TokenExchangeState,
    SignInResource,
)

def mock_TokenExchangeState(
        self,
        mocker,
        get_encoded_state_return="encoded_state",
    ):
    
    mock_token_exchange_state = mocker.Mock(spec=TokenExchangeState)
    mock_token_exchange_state.get_encoded_state = mocker.Mock(
        return_value=get_encoded_state_return
    )
    return mock_token_exchange_state

# def mock_SignInResource(
#     self,
#     mocker,
#     sign_in_link="https://example.com/signin",
#     token_exchange_state=None,
# ):
#     mock_sign_in_resource = mocker.Mock(spec=SignInResource)
#     mock_sign_in_resource.sign_in_link.return_value = sign_in_link
#     mock_sign_in_resource.token_exchange_state = token_exchange_state
#     return mock_sign_in_resource