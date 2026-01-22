from contextlib import asynccontextmanager

class TestChannel:

    @asynccontextmanager
    async def listen(self):
        yield self

    async def pop(self):
        pass