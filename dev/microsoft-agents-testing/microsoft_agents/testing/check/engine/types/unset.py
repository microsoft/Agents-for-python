# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .readonly import Readonly

class _Unset(Readonly):
    """A class representing an unset value."""
    
    def get(self, *args, **kwargs):
        """Returns the singleton instance when accessed as a method."""
        return self
    
    def __getattr__(self, name, *args, **kwargs):
        """Returns the singleton instance when accessed as an attribute."""
        return self
    
    def __getitem__(self, key, *args, **kwargs):
        """Returns the singleton instance when accessed as an item."""
        return self
    
    def __bool__(self):
        """Returns False when converted to a boolean."""
        return False
    
    def __repr__(self):
        """Returns 'Unset' when represented."""
        return "Unset"
    
    def __str__(self):
        """Returns 'Unset' when converted to a string."""
        return repr(self)
    
Unset = _Unset()