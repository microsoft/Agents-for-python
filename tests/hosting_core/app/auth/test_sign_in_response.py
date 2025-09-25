from microsoft_agents.hosting.core import SignInResponse, FlowStateTag


def test_sign_in_response_sign_in_complete():
    assert SignInResponse(tag=FlowStateTag.BEGIN).sign_in_complete() == False
    assert SignInResponse(tag=FlowStateTag.CONTINUE).sign_in_complete() == False
    assert SignInResponse(tag=FlowStateTag.FAILURE).sign_in_complete() == False
    assert SignInResponse().sign_in_complete() == False
    assert SignInResponse(tag=FlowStateTag.NOT_STARTED).sign_in_complete() == True
    assert SignInResponse(tag=FlowStateTag.COMPLETE).sign_in_complete() == True
