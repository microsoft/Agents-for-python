import pytest

from ..core import integration_test_suite_factory
from ..samples import QuickstartSample

TestSuiteBase = integration_test_suite_factory(QuickstartSample)

class TestQuickstart(TestSuiteBase):
    
    @pytest.mark.asyncio
    async def test_quickstart_functionality(self):
        pass