from typing import Any

from .underscore import (
    PlaceholderType,
    Underscore,
)

# Anonymous placeholder - consumes args in order
_ = Underscore()

# Indexed placeholders - refer to specific positional args
_0 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=0)
_1 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=1)
_2 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=2)
_3 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=3)
_4 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=4)

# Custom indexed placeholder factory
_n = lambda index: Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=index)

class _VarFactory:
    """
    Factory for creating indexed and named placeholders.
    
    Usage:
        _var[0]      -> indexed placeholder for arg 0
        _var[1]      -> indexed placeholder for arg 1
        _var["name"] -> named placeholder for kwarg "name"
        _var.name    -> named placeholder for kwarg "name" (attribute syntax)
    """
    
    def __getitem__(self, key: Any) -> Underscore:
        """Create a placeholder via indexing."""
        if isinstance(key, int):
            return Underscore(
                placeholder_type=PlaceholderType.INDEXED,
                placeholder_id=key,
            )
        elif isinstance(key, str):
            return Underscore(
                placeholder_type=PlaceholderType.NAMED,
                placeholder_id=key,
            )
        else:
            raise TypeError(
                f"_var key must be int (for indexed) or str (for named), "
                f"got {type(key).__name__}"
            )
    
    def __getattr__(self, name: str) -> Underscore:
        """Create a named placeholder via attribute access."""
        if name.startswith('_'):
            raise AttributeError(f"Cannot create placeholder with name '{name}'")
        return Underscore(
            placeholder_type=PlaceholderType.NAMED,
            placeholder_id=name,
        )
    
    def __repr__(self) -> str:
        return "_var"

# Factory for creating placeholders dynamically
_var = _VarFactory()