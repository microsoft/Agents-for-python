import pytest
from microsoft_agents.activity import RoleTypes


@pytest.fixture(params=[RoleTypes.user, RoleTypes.skill, RoleTypes.agent])
def non_agentic_role(request):
    return request.param


@pytest.fixture(params=[RoleTypes.agentic_user, RoleTypes.agentic_identity])
def agentic_role(request):
    return request.param
