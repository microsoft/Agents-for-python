import json

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core.app.oauth._sign_in_state import _SignInState


def test_sign_in_state_serialization_deserialization(tmp_path):
    original_state = _SignInState(
        active_handler_id="handler_123",
        continuation_activity=Activity(
            type="message",
            id="activity_456",
            timestamp="2024-01-01T12:00:00Z",
            service_url="https://service.url",
            channel_id="channel_789",
            from_property={"id": "user_1"},
            conversation={"id": "conv_1"},
            recipient={"id": "bot_1"},
            text="Hello, World!",
        ),
    )

    # Serialize to JSON
    json_data = original_state.store_item_to_json()

    # Deserialize back to _SignInState
    deserialized_state = _SignInState.from_json_to_store_item(json_data)

    # Assert equality
    assert deserialized_state.active_handler_id == original_state.active_handler_id
    assert (
        deserialized_state.continuation_activity == original_state.continuation_activity
    )

    with open(tmp_path / "sign_in_state.json", "w") as f:
        json.dump(json_data, f)

    with open(tmp_path / "sign_in_state.json", "r") as f:
        loaded_json_data = json.load(f)

    loaded_state = _SignInState.from_json_to_store_item(loaded_json_data)
    assert loaded_state.active_handler_id == original_state.active_handler_id
    assert loaded_state.continuation_activity == original_state.continuation_activity
