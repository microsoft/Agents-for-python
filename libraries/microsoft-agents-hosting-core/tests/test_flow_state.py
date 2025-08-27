from datetime import datetime

import pytest

from microsoft_agents.hosting.core.oauth.flow_state import FlowState, FlowStateTag


class TestFlowState:

    @pytest.mark.parametrize(
        "original_flow_state, refresh_to_not_started",
        [
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.FAILURE,
                    attempts_remaining=-1,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
        ],
    )
    def test_refresh(self, original_flow_state, refresh_to_not_started):
        new_flow_state = original_flow_state.model_copy()
        new_flow_state.refresh()
        expected_flow_state = original_flow_state.model_copy()
        if refresh_to_not_started:
            expected_flow_state.tag = FlowStateTag.NOT_STARTED
        assert new_flow_state == expected_flow_state

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.FAILURE,
                    attempts_remaining=-1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
        ],
    )
    def test_is_expired(self, flow_state, expected):
        assert flow_state.is_expired() == expected

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.FAILURE,
                    attempts_remaining=-1,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
        ],
    )
    def test_reached_max_attempts(self, flow_state, expected):
        assert flow_state.reached_max_attempts() == expected

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.FAILURE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=2,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                True,
            ),
            (
                FlowState(
                    tag=FlowStateTag.BEGIN,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.COMPLETE,
                    attempts_remaining=-1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.FAILURE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                FlowState(
                    tag=FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                True,
            ),
        ],
    )
    def test_is_active(self, flow_state, expected):
        assert flow_state.is_active() == expected
