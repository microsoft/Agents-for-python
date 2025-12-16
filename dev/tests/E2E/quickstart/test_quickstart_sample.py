import pytest

from microsoft_agents.testing import (
    Integration,
    AiohttpEnvironment,
)

from ...samples import QuickstartSample

class TestQuickstartDirectline(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment
