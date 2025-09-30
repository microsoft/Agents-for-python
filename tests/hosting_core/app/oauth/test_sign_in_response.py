from microsoft_agents.hosting.core.app.oauth import _SignInResponse
from microsoft_agents.hosting.core._oauth import _FlowStateTag

def test_sign_in_response_sign_in_complete():
    assert _SignInResponse(tag=_FlowStateTag.BEGIN).sign_in_complete() == False
    assert _SignInResponse(tag=_FlowStateTag.CONTINUE).sign_in_complete() == False
    assert _SignInResponse(tag=_FlowStateTag.FAILURE).sign_in_complete() == False
    assert _SignInResponse().sign_in_complete() == False
    assert _SignInResponse(tag=_FlowStateTag.NOT_STARTED).sign_in_complete() == True
    assert _SignInResponse(tag=_FlowStateTag.COMPLETE).sign_in_complete() == True
