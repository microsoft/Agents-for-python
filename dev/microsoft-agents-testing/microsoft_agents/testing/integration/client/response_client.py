class ResponseClient:

    async def start_server(self):
        pass
    
    async def close(self):
        pass

    async def __aenter__(self):
        await self.start_server()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()