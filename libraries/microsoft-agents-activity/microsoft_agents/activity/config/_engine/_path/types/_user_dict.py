# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import collections.abc


class _UserDict(dict):
    """Native dictionary base with subclass-aware mutation helpers.

    Construction and copies own their outer storage while sharing nested values.
    """

    def __init__(self, data=None, /, **kwargs):
        super().__init__()
        if data is not None:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    # Native dict mutators bypass subclass lookup and mutation hooks.
    update = collections.abc.MutableMapping.update
    setdefault = collections.abc.MutableMapping.setdefault
    pop = collections.abc.MutableMapping.pop
    popitem = collections.abc.MutableMapping.popitem
    clear = collections.abc.MutableMapping.clear

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

    def __or__(self, other):
        merged = super().__or__(other)
        if merged is NotImplemented:
            return NotImplemented
        return self.__class__(merged)

    def __ror__(self, other):
        merged = super().__ror__(other)
        if merged is NotImplemented:
            return NotImplemented
        return self.__class__(merged)

    def __ior__(self, other):
        self.update(other)
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        dict.__init__(inst, self)
        inst.__dict__.update(self.__dict__)
        return inst

    def copy(self):
        import copy

        return copy.copy(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d
