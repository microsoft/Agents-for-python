# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Unset - Sentinel value for representing missing/unset values.

Provides a singleton that represents the absence of a value, distinct from None.
Useful for distinguishing between \"not set\" and \"explicitly set to None\".
"""

from __future__ import annotations

from .readonly import Readonly


class Unset(Readonly):
    """Singleton representing an unset/missing value.
    
    All attribute access, item access, and method calls return the Unset
    instance itself, allowing safe chained access on potentially missing data.
    
    Note: The class is instantiated as a singleton at module load time.
    """
    
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
    
    def __contains__(self, item):
        """Returns False for any containment check."""
        return False
    
    def __iter__(self):
        """Returns an empty iterator to prevent iteration hangs."""
        return iter([])
        
Unset = Unset()