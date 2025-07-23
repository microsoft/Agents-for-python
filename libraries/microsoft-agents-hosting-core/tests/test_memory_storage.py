from microsoft.agents.hosting.core.storage.memory_storage import MemoryStorage
from microsoft.agents.hosting.core.storage.storage_test_utils import CRUDStorageTests


class TestMemoryStorage(CRUDStorageTests):
    async def storage(self, initial_data=None):
        data = {
            key: value.store_item_to_json()
            for key, value in (initial_data or {}).items()
        }
        return MemoryStorage(data)
