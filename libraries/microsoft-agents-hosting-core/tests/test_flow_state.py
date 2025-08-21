from datetime import datetime

import pytest

from microsoft.agents.hosting.core.oauth.flow_state import FlowState, FlowStateTag

class TestFlowState:

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=0, expires_at=datetime.now().timestamp()),
             True),
            (FlowState(tag=FlowStateTag.BEGIN, attempts_remaining=1, expires_at=datetime.now().timestamp()),
             True),
            (FlowState(tag=FlowStateTag.COMPLETE, attempts_remaining=0, expires_at=datetime.now().timestamp()-100),
             True),
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=1, expires_at=datetime.now().timestamp()+1000),
             False),
            (FlowState(tag=FlowStateTag.FAILURE, attempts_remaining=-1, expires_at=datetime.now().timestamp()+1000),
             False),
        ]
    )
    def test_is_expired(self, flow_state, expected):
        assert flow_state.is_expired() == expected

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=0, expires_at=datetime.now().timestamp()),
             True),
            (FlowState(tag=FlowStateTag.BEGIN, attempts_remaining=1, expires_at=datetime.now().timestamp()),
             False),
            (FlowState(tag=FlowStateTag.COMPLETE, attempts_remaining=0, expires_at=datetime.now().timestamp()-100),
             True),
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=1, expires_at=datetime.now().timestamp()-100),
             False),
            (FlowState(tag=FlowStateTag.FAILURE, attempts_remaining=-1, expires_at=datetime.now().timestamp()),
             True),
        ]
    )
    def test_reached_max_attempts(self, flow_state, expected):
        assert flow_state.reached_max_attempts() == expected

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=0, expires_at=datetime.now().timestamp()),
             False),
            (FlowState(tag=FlowStateTag.BEGIN, attempts_remaining=1, expires_at=datetime.now().timestamp()),
             False),
            (FlowState(tag=FlowStateTag.COMPLETE, attempts_remaining=0, expires_at=datetime.now().timestamp()-100),
             False),
            (FlowState(tag=FlowStateTag.FAILURE, attempts_remaining=1, expires_at=datetime.now().timestamp()-100),
             False),
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=2, expires_at=datetime.now().timestamp()+1000),
             True),
            (FlowState(tag=FlowStateTag.BEGIN, attempts_remaining=0, expires_at=datetime.now().timestamp()+1000),
             False),
            (FlowState(tag=FlowStateTag.COMPLETE, attempts_remaining=-1, expires_at=datetime.now().timestamp()+1000),
             False),
            (FlowState(tag=FlowStateTag.FAILURE, attempts_remaining=1, expires_at=datetime.now().timestamp()+1000),
             False),
            (FlowState(tag=FlowStateTag.CONTINUE, attempts_remaining=1, expires_at=datetime.now().timestamp()+1000),
             True)
        ]
    )
    def test_is_active(self, flow_state, expected):
        assert flow_state.is_active() == expected