from microsoft_agents.hosting.core.storage.memory_storage import MemoryStorage
from tests._common.storage.utils import CRUDStorageTests

class TestMemoryStorage(CRUDStorageTests):
    async def storage(self, initial_data=None):
        data = {
            key: value.store_item_to_json()
            for key, value in (initial_data or {}).items()
        }
        return MemoryStorage(data)
