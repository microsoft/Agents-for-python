import pytest
from ..testing_environment import TestingEnvironment, MockTestingEnvironment

from ..samples.quickstart import main

class TestQuickstart(MockTestingEnvironment):
    async def test_quickstart(self):
        main(self.testenv)

        self.testenv.adapter.send_activity("Hello World")

class TestQuickstartOtherEnv(SampleEnvironment):
    async def test_quickstart(self):
        with pytest.raises(Exception):
            main(self.testenv)
            self.testenv.adapter.send_activity("Hello World")