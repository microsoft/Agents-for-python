import pytest

from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ....samples import BasicSample

@ddt("tests/data_driven/basic/directline")
class TestBasicDirectline(Integration):
    _sample_cls = BasicSample
    _environment_cls = AiohttpEnvironment

@ddt("tests/data_driven/basic/directline")
@pytest.mark.skipif(True, reason="Skipping external agent tests for now.")
class TestBasicExternalDirectline(Integration):
    ...