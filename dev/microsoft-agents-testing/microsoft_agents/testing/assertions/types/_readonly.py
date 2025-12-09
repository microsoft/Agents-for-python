class _Readonly:
    """A mixin class that makes all attributes of a class readonly."""
    
    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot set attribute '{name}' on {type(self).__name__}")

    def __delattr__(self, name):
        raise AttributeError(f"Cannot delete attribute '{name}' on {type(self).__name__}")
    
    def __setitem__(self, key, value):
        raise AttributeError(f"Cannot set item '{key}' on {type(self).__name__}")
    
    def __delitem__(self, key):
        raise AttributeError(f"Cannot delete item '{key}' on {type(self).__name__}")