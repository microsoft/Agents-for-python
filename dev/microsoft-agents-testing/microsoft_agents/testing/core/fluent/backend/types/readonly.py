# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

\"\"\"Readonly - Mixin for creating immutable objects.

Provides a base class that prevents attribute and item modification,
useful for creating singleton or constant objects.
\"\"\"

from typing import Any


class Readonly:
    \"\"\"Mixin that makes all attributes and items read-only.
    
    Any attempt to set or delete attributes/items will raise AttributeError.
    \"\"\"
    
    def __setattr__(self, name: str, value: Any):
        """Prevent setting attributes on the readonly object."""
        raise AttributeError(f"Cannot set attribute '{name}' on {type(self).__name__}")

    def __delattr__(self, name: str):
        """Prevent deleting attributes on the readonly object."""
        raise AttributeError(f"Cannot delete attribute '{name}' on {type(self).__name__}")
    
    def __setitem__(self, key: str, value: Any):
        """Prevent setting items on the readonly object."""
        raise AttributeError(f"Cannot set item '{key}' on {type(self).__name__}")
    
    def __delitem__(self, key: str):
        """Prevent deleting items on the readonly object."""
        raise AttributeError(f"Cannot delete item '{key}' on {type(self).__name__}")