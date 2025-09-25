import pytest

from microsoft_agents.hosting.core.app.auth import SignInState

from ._common import testing_Activity, testing_TurnContext

class TestSignInState:

    def test_init(self):
        state = SignInState()
        assert state.tokens == {}
        assert state.continuation_activity is None

    def test_init_with_values(self):
        activity = testing_Activity()
        state = SignInState({
            "handler": "some_token"
        }, activity)
        assert state.tokens == {"handler": "some_token"}
        assert state.continuation_activity == activity

    def test_from_json_to_store_item(self):
        tokens = {
            "some_handler": "some_token",
            "other_handler": "other_token"
        }
        activity = testing_Activity()
        data = {
            "tokens": tokens,
            "continuation_activity": activity
        }
        state = SignInState.from_json_to_store_item(data)
        assert state.tokens == tokens
        assert state.continuation_activity == activity

    def test_store_item_to_json(self):
        tokens = {
            "some_handler": "some_token",
            "other_handler": "other_token"
        }
        activity = testing_Activity()
        state = SignInState(tokens, activity)
        json_data = state.store_item_to_json()
        assert json_data["tokens"] == tokens
        assert json_data["continuation_activity"] == activity

    @pytest.mark.parametrize("tokens, active_handler", [
        [{}, ""],
        [{"some_handler": ""}, "some_handler"],
        [{"some_handler": "some_token"}, ""],
        [{"some_handler": "some_value", "other_handler": ""}, "other_handler"],
        [{"some_handler": "some_value", "other_handler": "other_value"}, ""],
        [{"some_handler": "some_value", "another_handler": "", "wow": "wow"}, "another_handler"],
    ])
    def test_active_handler(self, tokens, active_handler):
        state = SignInState(tokens)
        assert state.active_handler() == active_handler