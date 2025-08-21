from datetime import datetime

from microsoft.agents.hosting.core.storage.storage_test_utils import MockStoreItem
from microsoft.agents.hosting.core.oauth.flow_state import FlowState, FlowStateTag

MS_APP_ID = "__ms_app_id"
CHANNEL_ID = "__channel_id"
USER_ID = "__user_id"
ABS_OAUTH_CONNECTION_NAME = "__connection_name"
RES_TOKEN = "__res_token"

DEF_ARGS = {
    "ms_app_id": MS_APP_ID,
    "channel_id": CHANNEL_ID,
    "user_id": USER_ID,
    "connection": ABS_OAUTH_CONNECTION_NAME
}

class FLOW_STATES:

    STARTED_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.BEGIN,
                attempts_remaining=1,
                user_token="____",
                expires_at=datetime.now().timestamp() + 1000000
            )
    STARTED_FLOW_ONE_RETRY = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.BEGIN,
                attempts_remaining=2,
                user_token="____",
                expires_at=datetime.now().timestamp() + 1000000
            )
    ACTIVE_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.CONTINUE,
                attempts_remaining=2,
                user_token="__token",
                expires_at=datetime.now().timestamp() + 1000000
            )
    ACTIVE_FLOW_ONE_RETRY = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.CONTINUE,
                attempts_remaining=1,
                user_token="__token",
                expires_at=datetime.now().timestamp() + 1000000
            )
    ACTIVE_EXP_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.CONTINUE,
                attempts_remaining=2,
                user_token="__token",
                expires_at=datetime.now().timestamp()
            )
    COMPLETED_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.COMPLETE,
                attempts_remaining=2,
                user_token="test_token",
                expires_at=datetime.now().timestamp() + 1000000
            )
    FAIL_BY_ATTEMPTS_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.FAILURE,
                attempts_remaining=0,
                expires_at=datetime.now().timestamp() + 1000000
            )

    FAIL_BY_EXP_FLOW = FlowState(
                **DEF_ARGS,
                tag=FlowStateTag.FAILURE,
                attempts_remaining=2,
                expires_at=0
            )

    @staticmethod
    def clone_state_list(lst):
        return [ flow_state.model_copy() for flow_state in lst ]

    @staticmethod
    def ALL():
        return FLOW_STATES.clone_state_list([
            FLOW_STATES.STARTED_FLOW,
            FLOW_STATES.STARTED_FLOW_ONE_RETRY,
            FLOW_STATES.ACTIVE_FLOW,
            FLOW_STATES.ACTIVE_FLOW_ONE_RETRY,
            FLOW_STATES.ACTIVE_EXP_FLOW,
            FLOW_STATES.COMPLETED_FLOW,
            FLOW_STATES.FAIL_BY_ATTEMPTS_FLOW,
            FLOW_STATES.FAIL_BY_EXP_FLOW
        ])

    @staticmethod
    def FAILED():
        return FLOW_STATES.clone_state_list([
            FLOW_STATES.ACTIVE_EXP_FLOW,
            FLOW_STATES.FAIL_BY_ATTEMPTS_FLOW,
            FLOW_STATES.FAIL_BY_EXP_FLOW
        ])

    @staticmethod
    def ACTIVE():
        return FLOW_STATES.clone_state_list([
            FLOW_STATES.STARTED_FLOW,
            FLOW_STATES.STARTED_FLOW_ONE_RETRY,
            FLOW_STATES.ACTIVE_FLOW,
            FLOW_STATES.ACTIVE_FLOW_ONE_RETRY,
        ])

    @staticmethod
    def INACTIVE():
        return FLOW_STATES.clone_state_list([
            FLOW_STATES.ACTIVE_EXP_FLOW,
            FLOW_STATES.COMPLETED_FLOW,
            FLOW_STATES.FAIL_BY_ATTEMPTS_FLOW,
            FLOW_STATES.FAIL_BY_EXP_FLOW
        ])

def flow_key(channel_id, user_id, handler_id):
    return f"auth/{channel_id}/{user_id}/{handler_id}"

def update_flow_state_handler(flow_state, handler):
    flow_state = flow_state.model_copy()
    flow_state.auth_handler_id = handler
    return flow_state
    
STORAGE_SAMPLE_DICT = {
    "user_id": MockStoreItem({"id": "123"}),
    "session_id": MockStoreItem({"id": "abc"}),
    flow_key("webchat", "Alice", "graph"): update_flow_state_handler(FLOW_STATES.COMPLETED_FLOW.model_copy(), "graph"),
    flow_key("webchat", "Alice", "github"): update_flow_state_handler(FLOW_STATES.ACTIVE_FLOW_ONE_RETRY.model_copy(), "github"),
    flow_key("teams", "Alice", "graph"): update_flow_state_handler(FLOW_STATES.STARTED_FLOW.model_copy(), "graph"),
    flow_key("webchat", "Bob", "graph"): update_flow_state_handler(FLOW_STATES.ACTIVE_EXP_FLOW.model_copy(), "graph"),
    flow_key("teams", "Bob", "slack"): update_flow_state_handler(FLOW_STATES.STARTED_FLOW.model_copy(), "slack"),
    flow_key("webchat", "Chuck", "github"): update_flow_state_handler(FLOW_STATES.FAIL_BY_ATTEMPTS_FLOW.model_copy(), "github"),
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