import pytest

from microsoft.agents.storage.item_storage_base import ItemStorageBase
from microsoft.agents.storage import StoreItem

class ItemStorageTestSuite(StorageTestSuiteBase):

    class ItemStorageImpl(ItemStorageBase):

        def read_item(self, key: str):
            pass

        def read(self):
            pass
            
        def write_item(self, item: StoreItem):
            pass

        def delete_item(self, key: str):
            pass

    @pytest.mark.asyncio
    async def test_read_raw_item(storage_pair, read_item_key):
        storage, baseline = storage_pair
        async with baseline.check_unchanged:
            expected = baseline.raw_read_item(read_item_key)
            item = await storage.read_raw_item(read_item_key)
        assert item == expected

    @pytest.mark.asyncio
    async def test_read_raw_error(storage_pair):
        storage, baseline = storage_pair
        with baseline.check_unchanged:
            with pytest.raises(Exception):
                await storage.read_raw_item(None)
            with pytest.raises(Exception):
                await storage.read_raw_item("")

    @pytest.mark.asyncio
    async def test_read():
        storage, baseline = storage_pair
        items = await check_unchanged(storage.read(, target_cls=MockStoreItem), baseline)
        assert items == list(baseline.values())

    def test_read_error():
        pass
        
    def test_read_item():
        pass

    def test_read():
        pass

    def test_write():
        pass

    def test_delete():
        pass

    def test_read_errors():
        pass

    def test_write_errors():
        pass

    def test_delete_errors():
        pass

class ItemStorageBaseTests:

    pass

    def test_