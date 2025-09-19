from .flow_states import FLOW_STATES, FlowState, update_flow_state_handler

STORAGE_SAMPLE_DICT = {
    "user_id": MockStoreItem({"id": "123"}),
    "session_id": MockStoreItem({"id": "abc"}),
    flow_key("webchat", "Alice", "graph"): update_flow_state_handler(
        FLOW_STATES.COMPLETED_FLOW.model_copy(), "graph"
    ),
    flow_key("webchat", "Alice", "github"): update_flow_state_handler(
        FLOW_STATES.ACTIVE_FLOW_ONE_RETRY.model_copy(), "github"
    ),
    flow_key("teams", "Alice", "graph"): update_flow_state_handler(
        FLOW_STATES.STARTED_FLOW.model_copy(), "graph"
    ),
    flow_key("webchat", "Bob", "graph"): update_flow_state_handler(
        FLOW_STATES.ACTIVE_EXP_FLOW.model_copy(), "graph"
    ),
    flow_key("teams", "Bob", "slack"): update_flow_state_handler(
        FLOW_STATES.STARTED_FLOW.model_copy(), "slack"
    ),
    flow_key("webchat", "Chuck", "github"): update_flow_state_handler(
        FLOW_STATES.FAIL_BY_ATTEMPTS_FLOW.model_copy(), "github"
    ),
}

def STORAGE_INIT_DATA():
    data = STORAGE_SAMPLE_DICT.copy()
    for key, value in data.items():
        data[key] = value.model_copy() if isinstance(value, FlowState) else value
    return data


def update_data_with_flow_state(data, channel_id, user_id, auth_handler_id, flow_state):
    data = data.copy()
    key = f"auth/{channel_id}/{user_id}/{auth_handler_id}"
    data[key] = flow_state.model_copy()
    return data
