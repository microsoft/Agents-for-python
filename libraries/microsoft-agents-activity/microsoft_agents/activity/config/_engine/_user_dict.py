import collections.abc


class _UserDict(collections.abc.MutableMapping):

    # Start by filling-out the abstract methods
    def __init__(self, data=None, _make_copy: bool = True, /, **kwargs):
        self._data = {}
        if data is not None:
            if _make_copy:
                self.update(data)
            else:
                self._data = data
        if kwargs:
            self.update(kwargs)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key, item):
        self._data[key] = item

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    # Modify __contains__ and get() to work like dict
    # does when __missing__ is present.
    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default


    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self):
        return repr(self._data)

    def __or__(self, other):
        if isinstance(other, _UserDict):
            return self.__class__(self._data | other._data)
        if isinstance(other, dict):
            return self.__class__(self._data | other)
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, _UserDict):
            return self.__class__(other._data | self._data)
        if isinstance(other, dict):
            return self.__class__(other | self._data)
        return NotImplemented

    def __ior__(self, other):
        if isinstance(other, _UserDict):
            self._data |= other._data
        else:
            self._data |= other
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_data"] = self.__dict__["_data"].copy()
        return inst

    def copy(self):
        if self.__class__ is _UserDict:
            return _UserDict(self._data.copy())
        import copy
        data = self._data
        try:
            self._data = {}
            c = copy.copy(self)
        finally:
            self._data = data
        c.update(self)
        return c

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

class _NoCopyUserDict(_UserDict):
    def __init__(self, dict=None, **kwargs):
        super().__init__(dict, _make_copy=False, **kwargs)