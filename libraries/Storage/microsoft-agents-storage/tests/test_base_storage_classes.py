class TestItemStorageBase:
    
    class ItemStorageImpl(ItemStorageBase):
        def __init__(self):
            super().__init__()
            self.store = {}
    
        async def _read_item(self, key: str, **kwargs) -> Union[JSON, None]:
            return self.store.get(key, None)
    
        async def _write_item(self, key: str, item: JSON, **kwargs) -> None:
            self.store[key] = item
    
        async def _delete_item(self, key: str) -> None:
            if key in self.store:
                del self.store[key]

class TestAutoStorageBase:
    
    class AutoStorageImpl(AutoStorageBase):
        def __init__(self):
            super().__init__()
            self.store = {}
    
        async def _read_item(self, key: str, **kwargs) -> Union[JSON, None]:
            return self.store.get(key, None)
    
        async def _write_item(self, key: str, item: JSON, **kwargs) -> None:
            self.store[key] = item
    
        async def _delete_item(self, key: str) -> None:
            if key in self.store:
                del self.store[key]




class TestItemStorageBase:
    
    # class ItemStorageImpl(ItemStorageBase):
    #     def __init__(self):
    #         super().__init__()
    #         self.store = {}
    
    #     async def _read_item(self, key: str, **kwargs) -> Union[JSON, None]:
    #         return self.store.get(key, None)
    
    #     async def _write_item(self, key: str, item: JSON, **kwargs) -> None:
    #         self.store[key] = item
    
    #     async def _delete_item(self, key: str) -> None:
    #         if key in self.store:
    #             del self.store[key]


