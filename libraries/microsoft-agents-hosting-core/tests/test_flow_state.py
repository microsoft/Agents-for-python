from datetime import datetime

import pytest

from microsoft.agents.hosting.core.oauth.flow_state import FlowState, FlowStateTag

class TestFlowState:

    def test_refresh_to_failure_expired(self):
        """Test that the flow state refreshes to failure when expired."""
        flow_state = FlowState(
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=1,
            expires_at=datetime.now().timestamp()
        )
        flow_state.refresh()
        assert flow_state.tag == FlowStateTag.FAILURE

    def test_refresh_to_failure_max_attempts(self):
        """Test that the flow state refreshes to failure when max attempts reached."""
        flow_state = FlowState(
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=0,
        )
        flow_state.refresh()
        assert flow_state.tag == FlowStateTag.FAILURE

    def test_refresh_unchanged_continue(self):
        """Test that the flow state remains unchanged when refreshed with a valid CONTINUE state"""
        flow_state = FlowState(
            tag=FlowStateTag.CONTINUE,
            attempts_remaining=1,
            expires_at=datetime.now().timestamp() + 10000
        )
        prev_tag = flow_state.tag
        flow_state.refresh()
        assert flow_state.tag == prev_tag

    def test_refresh_unchanged_begin(self):
        """Test that the flow state remains unchanged when refreshed with a valid BEGIN state"""
        flow_state = FlowState(
            tag=FlowStateTag.BEGIN,
            attempts_remaining=10,
            expires_at=datetime.now().timestamp() + 30000
        )
        prev_tag = flow_state.tag
        flow_state.refresh()
        assert flow_state.tag == prev_tag

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