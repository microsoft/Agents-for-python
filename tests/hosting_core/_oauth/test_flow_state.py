import pytest
from datetime import datetime
from microsoft_agents.hosting.core._oauth._flow_state import _FlowState, _FlowStateTag


class TestFlowState:
    @pytest.mark.parametrize(
        "original_flow_state, refresh_to_not_started",
        [
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.FAILURE,
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
            expected_flow_state.tag = _FlowStateTag.NOT_STARTED
        assert new_flow_state == expected_flow_state

    @pytest.mark.parametrize(
        "flow_state, expected",
        [
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.FAILURE,
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
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.FAILURE,
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
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.BEGIN,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp(),
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.COMPLETE,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.FAILURE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() - 100,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=2,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                True,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.BEGIN,
                    attempts_remaining=0,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.COMPLETE,
                    attempts_remaining=-1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.FAILURE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                False,
            ),
            (
                _FlowState(
                    tag=_FlowStateTag.CONTINUE,
                    attempts_remaining=1,
                    expiration=datetime.now().timestamp() + 1000,
                ),
                True,
            ),
        ],
    )
    def test_is_active(self, flow_state, expected):
        assert flow_state.is_active() == expected
