from microsoft.agents.storage.memory_storage import MemoryStorage
from microsoft.agents.storage.storage_test_utils import CRUDStorageTests, StorageMock

class MemoryStorageMock(StorageMock):

    def __init__(self, initial_data: dict = None):

        data = {
            key: value.store_item_to_json() for key, value in (initial_data or {}).items()
        }
        self.storage = MemoryStorage(data)

    def get_backing_store(self):
        return self.storage

class TestMemoryStorage(CRUDStorageTests):
    
    async def storage(self, initial_state = None):
        return MemoryStorageMock(initial_state)