# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations


class _UserList(list):
    """Native list base retaining subclass types for copies and operators.

    Construction, copies, and slices copy the outer list while sharing elements.
    """

    def __init__(self, initlist=None):
        super().__init__(() if initlist is None else initlist)

    def __getitem__(self, i):
        value = super().__getitem__(i)
        if isinstance(i, slice):
            return self.__class__(value)
        return value

    def __add__(self, other):
        if not isinstance(other, list):
            other = list(other)
        return self.__class__(super().__add__(other))

    def __radd__(self, other):
        if not isinstance(other, list):
            other = list(other)
        return self.__class__(list.__add__(other, self))

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __mul__(self, n):
        return self.__class__(super().__mul__(n))

    __rmul__ = __mul__

    def __imul__(self, n):
        super().__imul__(n)
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        list.__init__(inst, self)
        inst.__dict__.update(self.__dict__)
        return inst

    def copy(self):
        return self.__class__(self)
