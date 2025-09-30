from tests._common.storage import MockStoreItem

from .test_flow_data import (
    TEST_FLOW_DATA,
    _FlowState,
    update_flow_state_handler,
    flow_key,
)

FLOW_DATA = TEST_FLOW_DATA()


class TEST_STORAGE_DATA:
    def __init__(self):

        self.dict = {
            "user_id": MockStoreItem({"id": "123"}),
            "session_id": MockStoreItem({"id": "abc"}),
            flow_key("webchat", "Alice", "graph"): update_flow_state_handler(
                FLOW_DATA.completed, "graph"
            ),
            flow_key("webchat", "Alice", "github"): update_flow_state_handler(
                FLOW_DATA.active_one_retry, "github"
            ),
            flow_key("teams", "Alice", "graph"): update_flow_state_handler(
                FLOW_DATA.started, "graph"
            ),
            flow_key("webchat", "Bob", "graph"): update_flow_state_handler(
                FLOW_DATA.active_exp, "graph"
            ),
            flow_key("teams", "Bob", "slack"): update_flow_state_handler(
                FLOW_DATA.started, "slack"
            ),
            flow_key("webchat", "Chuck", "github"): update_flow_state_handler(
                FLOW_DATA.fail_by_attempts, "github"
            ),
        }

    def get_init_data(self):
        data = self.dict.copy()
        for key, value in data.items():
            data[key] = value.model_copy() if isinstance(value, _FlowState) else value
        return data


def update_data_with_flow_state(data, channel_id, user_id, auth_handler_id, flow_state):
    data = data.copy()
    key = f"auth/{channel_id}/{user_id}/{auth_handler_id}"
    data[key] = flow_state.model_copy()
    return data
