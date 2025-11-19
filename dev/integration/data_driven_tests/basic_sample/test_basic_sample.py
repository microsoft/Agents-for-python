from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ...samples.basic_sample import BasicSample

@ddt("./directline")
class TestDirectLine(Integration):
    _sample_cls = BasicSample
    _environment_cls = AiohttpEnvironment

@ddt("./webchat")
class TestWebChat(Integration):
    _sample_cls = BasicSample
    _environment_cls = AiohttpEnvironment