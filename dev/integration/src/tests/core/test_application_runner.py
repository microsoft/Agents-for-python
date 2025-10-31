import pytest
from time import sleep

from ._common import SimpleRunner, OtherSimpleRunner

class TestApplicationRunner:

    @pytest.mark.asyncio
    async def test_simple_runner(self):

        app = {}
        runner = SimpleRunner(app)
        async with runner as r:
            sleep(0.1)
            assert runner is r
            assert app["running"] is True
        
        assert app["running"] is True

    @pytest.mark.asyncio
    async def test_other_simple_runner(self):

        app = {}
        runner = OtherSimpleRunner(app)
        async with runner as r:
            sleep(0.1)
            assert runner is r
            assert app["running"] is True
        
        assert app["running"] is False

    @pytest.mark.asyncio
    async def test_double_start(self):

        app = {}
        runner = SimpleRunner(app)
        async with runner:
            sleep(0.1)
            with pytest.raises(RuntimeError):
                async with runner:
                    pass