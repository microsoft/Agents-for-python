import pytest

from microsoft_agents.hosting.core._oauth import _FlowStateTag

from tests._common.data import FLOW_TEST_DATA

FLOW_STATES = FLOW_TEST_DATA()


class FlowStateFixtures:
    @pytest.fixture(params=FLOW_STATES.all_flows())
    def flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.failed_flows())
    def failed_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.inactive_flows())
    def inactive_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(
        params=[
            flow_state
            for flow_state in FLOW_STATES.inactive_flows()
            if flow_state.tag != _FlowStateTag.COMPLETE
        ]
    )
    def inactive_flow_state_not_completed(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.active_flows())
    def active_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(
        params=[
            flow_state
            for flow_state in FLOW_STATES.inactive_flows()
            if flow_state.tag != _FlowStateTag.COMPLETE
        ]
    )
    def sample_inactive_flow_state_not_completed(self, request):
        return request.param.model_copy()
