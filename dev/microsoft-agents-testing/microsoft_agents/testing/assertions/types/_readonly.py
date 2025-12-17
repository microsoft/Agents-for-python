class _Readonly:
    """A mixin class that makes all attributes of a class readonly."""
    
    def __setattr__(self, name, value):
        """Prevent setting attributes on the readonly object."""
        raise AttributeError(f"Cannot set attribute '{name}' on {type(self).__name__}")

    def __delattr__(self, name):
        """Prevent deleting attributes on the readonly object."""
        raise AttributeError(f"Cannot delete attribute '{name}' on {type(self).__name__}")
    
    def __setitem__(self, key, value):
        """Prevent setting items on the readonly object."""
        raise AttributeError(f"Cannot set item '{key}' on {type(self).__name__}")
    
    def __delitem__(self, key):
        """Prevent deleting items on the readonly object."""
        raise AttributeError(f"Cannot delete item '{key}' on {type(self).__name__}")