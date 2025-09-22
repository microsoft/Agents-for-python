from datetime import datetime

from microsoft_agents.hosting.core.oauth.flow_state import FlowState, FlowStateTag

from tests._common.storage import MockStoreItem
from tests._common.data.test_defaults import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

DEF_FLOW_ARGS = {
    "ms_app_id": DEFAULTS.ms_app_id,
    "channel_id": DEFAULTS.channel_id,
    "user_id": DEFAULTS.user_id,
    "connection": DEFAULTS.abs_oauth_connection_name,
}


class TEST_FLOW_DATA:
    def __init__(self):

        self.not_started = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.NOT_STARTED,
            attempts_remaining=1,
            user_token="____",
            expiration=datetime.now().timestamp() + 1000000,
        )

        self.started = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.BEGIN,
            attempts_remaining=1,
            user_token="____",
            expiration=datetime.now().timestamp() + 1000000,
        )

        self.started_one_retry = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.BEGIN,
            attempts_remaining=2,
            user_token="____",
            expiration=datetime.now().timestamp() + 1000000,
        )

        self.active = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=2,
            user_token="__token",
            expiration=datetime.now().timestamp() + 1000000,
        )

        self.active_one_retry = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=1,
            user_token="__token",
            expiration=datetime.now().timestamp() + 1000000,
        )
        self.active_exp = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=2,
            user_token="__token",
            expiration=datetime.now().timestamp(),
        )
        self.completed = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.COMPLETE,
            attempts_remaining=2,
            user_token="test_token",
            expiration=datetime.now().timestamp() + 1000000,
        )
        self.fail_by_attempts = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.FAILURE,
            attempts_remaining=0,
            expiration=datetime.now().timestamp() + 1000000,
        )

        self.fail_by_exp = FlowState(
            **DEF_FLOW_ARGS,
            tag=FlowStateTag.FAILURE,
            attempts_remaining=2,
            expiration=0,
        )

    @staticmethod
    def model_copy_list(lst):
        return [flow_state.model_copy() for flow_state in lst]

    def all_flows(self):
        return self.model_copy_list(
            [
                self.started,
                self.started_one_retry,
                self.active,
                self.active_one_retry,
                self.active_exp,
                self.completed,
                self.fail_by_attempts,
                self.fail_by_exp,
            ]
        )

    def failed_flows(self):
        return self.model_copy_list(
            [
                self.active_exp,
                self.fail_by_attempts,
                self.fail_by_exp,
            ]
        )

    def active_flows(self):
        return self.model_copy_list(
            [
                self.started,
                self.started_one_retry,
                self.active,
                self.active_one_retry,
            ]
        )

    def inactive_flows(self):
        return self.model_copy_list(
            [
                self.active_exp,
                self.completed,
                self.fail_by_attempts,
                self.fail_by_exp,
            ]
        )


def flow_key(channel_id, user_id, handler_id):
    return f"auth/{channel_id}/{user_id}/{handler_id}"


def update_flow_state_handler(flow_state, handler):
    flow_state = flow_state.model_copy()
    flow_state.auth_handler_id = handler
    return flow_state
