from datetime import datetime
from microsoft.agents.hosting.core.app.oauth.models import FlowState, FlowStateTag

class TEST_DEFAULTS:

    MS_APP_ID = "__ms_app_id"
    CHANNEL_ID = "__channel_id"
    USER_ID = "__user_id"
    ABS_OAUTH_CONNECTION_NAME = "__connection_name"
    RES_TOKEN = "__res_token"

    DEF_ARGS = {
        "ms_app_id": MS_APP_ID,
        "channel_id": CHANNEL_ID,
        "user_id": USER_ID,
        "abs_oauth_connection_name": ABS_OAUTH_CONNECTION_NAME
    }

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
    
    @classmethod
    def __format(cls, lst):
        return [ flow_state.model_copy() for flow_state in lst ]
    
    @classmethod
    def ALL(cls):
        return cls.__format([
            cls.STARTED_FLOW,
            cls.STARTED_FLOW_ONE_RETRY,
            cls.ACTIVE_FLOW,
            cls.ACTIVE_FLOW_ONE_RETRY,
            cls.ACTIVE_EXP_FLOW,
            cls.COMPLETED_FLOW,
            cls.FAIL_BY_ATTEMPTS_FLOW,
            cls.FAIL_BY_EXP_FLOW
        ])
    
    @classmethod
    def FAILED(cls):
        return cls.__format([
            cls.ACTIVE_EXP_FLOW,
            cls.FAIL_BY_ATTEMPTS_FLOW,
            cls.FAIL_BY_EXP_FLOW
        ])
    
    @classmethod
    def ACTIVE(cls):
        return cls.__format([
            cls.STARTED_FLOW,
            cls.STARTED_FLOW_ONE_RETRY,
            cls.ACTIVE_FLOW,
            cls.ACTIVE_FLOW_ONE_RETRY,
        ])
    
    @classmethod
    def INACTIVE(cls):
        return cls.__format([
            cls.ACTIVE_EXP_FLOW,
            cls.COMPLETED_FLOW,
            cls.FAIL_BY_ATTEMPTS_FLOW,
            cls.FAIL_BY_EXP_FLOW
        ])

def flow_key(channel_id, user_id, handler_id):
    return f"auth/{channel_id}/{user_id}/{handler_id}"
    
STORAGE_SAMPLE_DICT = {
    "user_id": "123",
    "session_id": "abc",
    flow_key("webchat", "Alice", "graph"): TEST_DEFAULTS.COMPLETED_FLOW.model_copy(),
    flow_key("webchat", "Alice", "github"): TEST_DEFAULTS.ACTIVE_FLOW_ONE_RETRY.model_copy(),
    flow_key("teams", "Alice", "graph"): TEST_DEFAULTS.STARTED_FLOW.model_copy(),
    flow_key("webchat", "Bob", "graph"): TEST_DEFAULTS.ACTIVE_EXP_FLOW.model_copy(),
    flow_key("teams", "Bob", "slack"): TEST_DEFAULTS.STARTED_FLOW.model_copy(),
    flow_key("webchat", "Chuck", "github"): TEST_DEFAULTS.FAIL_BY_ATTEMPTS_FLOW.model_copy(),
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