import pytest

from microsoft_agents.activity import Activity

@pytest.fixture
def activity():
    return Activity(type="message", text="Hello, World!")

@pytest.fixture(params=[
    Activity(type="message", text="Hello, World!"),
    {"type": "message", "text": "Hello, World!"}
])
def baseline(request):
    return request.param