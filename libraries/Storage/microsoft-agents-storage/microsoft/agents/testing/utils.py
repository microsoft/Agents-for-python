from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from microsoft.agents.storage import Storage, StoreItem, JSON
from microsoft.agents.storage.storage import ItemStorageBase, AutoStorageBase

def my_deepcopy(original):
    """Deep copy an object, including StoreItem instances."""

    iter_obj = None
    if isinstance(original, list):
        iter_obj = enumerate(original)
    elif isinstance(original, dict):
        iter_obj = original.items()
    elif isinstance(original, MockStoreItem):
        return original.deepcopy()
    else:
        return deepcopy(original)

    obj = {} if isinstance(original, dict) else ([None] * len(original))
    for key, value in iter_obj:
        obj[key] = my_deepcopy(value)
    return obj

def subsets(lst, n=-1):
    """Generate all subsets of a list up to length n. If n is -1, all subsets are generated.

    Only contiguous subsets are generated.
    """
    if n < 0:
        n = len(lst)
    subsets = []
    for i in range(len(lst) + 1):
        for j in range(0, i):
            if 1 <= i - j <= n:
                subsets.append(lst[j:i])
    return subsets
    
    

# class check_unchanged:
#     def __init__(self, awaitablebaseline):
#         self.state_before = baseline.state()
#     def __enter__(self):
#         elf.state_before = baseline.state()
#         return self.cr
#     def __exit__(self, type, value, traceback):
#         self.cr.restore()