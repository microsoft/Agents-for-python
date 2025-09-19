from tests._common.data import TESTING_FLOW_STATES

FLOW_STATES = TESTING_FLOW_STATES

class FlowStateFixtures:

    @pytest.fixture(params=FLOW_STATES.ALL())
    def flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.FAILED())
    def failed_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.INACTIVE())
    def inactive_flow_state(self, request):
        return request.param.model_copy()

    @pytest.fixture(
        params=[
            flow_state
            for flow_state in FLOW_STATES.INACTIVE()
            if flow_state.tag != FlowStateTag.COMPLETE
        ]
    )
    def inactive_flow_state_not_completed(self, request):
        return request.param.model_copy()

    @pytest.fixture(params=FLOW_STATES.ACTIVE())
    def active_flow_state(self, request):
        return request.param.model_copy()