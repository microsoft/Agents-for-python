class AutoStorageTestSuite(ItemStorageTestSuite):
    
    @pytest.mark.asyncio
    async def test_read_auto_item(storage_pair, read_item_key):
        pass

    @pytest.mark.asyncio
    async def test_read_auto_error(storage_pair):
        pass

    @pytest.mark.asyncio
    async def test_auto_deserializer(storage_pair):
        pass