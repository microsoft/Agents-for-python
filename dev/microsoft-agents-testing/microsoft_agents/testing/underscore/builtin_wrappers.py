from .underscore import Underscore, OperationType

# Deferred builtin wrappers
class _BuiltinWrapper:
    """Wraps a builtin to work with placeholders."""
    def __init__(self, func):
        self._func = func
    
    def __call__(self, *args, **kwargs):
        
        # If first arg is Underscore, compose with it
        if args and isinstance(args[0], Underscore):
            placeholder = args[0]
            remaining_args = args[1:]
            # Record: apply self._func to the resolved value
            return placeholder._copy_with((
                OperationType.APPLY_BUILTIN, 
                (self._func,) + remaining_args, 
                kwargs
            ))
        return self._func(*args, **kwargs)
    
    def __ror__(self, other):
        """Support pipe syntax: _ | _len"""
        return self(other)
    
    def __repr__(self):
        return f"_{self._func.__name__}"
    
def _make_check(func, repr_template: str):
    """
    Factory for creating check wrappers with nice repr.
    
    Args:
        func: A function that takes (*bound_args) and returns a predicate (x) -> bool
        repr_template: Format string for repr, e.g. "_isinstance({!r})"
    
    Usage:
        _isinstance = _make_check(
            lambda types: lambda x: isinstance(x, types),
            "_isinstance({!r})"
        )
    """
    class _Check:
        def __init__(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs
            self._predicate = func(*args, **kwargs)
        
        def __call__(self, placeholder):
            if isinstance(placeholder, Underscore):
                return placeholder._copy_with((
                    OperationType.APPLY_BUILTIN,
                    (self._predicate,),
                    {}
                ))
            return self._predicate(placeholder)
        
        def __ror__(self, other):
            return self(other)
        
        def __repr__(self):
            all_args = [repr(a) for a in self._args]
            all_args += [f"{k}={v!r}" for k, v in self._kwargs.items()]
            # Replace {!r} placeholders with actual args
            if "{!r}" in repr_template:
                return repr_template.format(*self._args)
            return f"{repr_template}({', '.join(all_args)})"
    
    return _Check

_len = _BuiltinWrapper(len)
_str = _BuiltinWrapper(str)
_int = _BuiltinWrapper(int)
_float = _BuiltinWrapper(float)
_bool = _BuiltinWrapper(bool)
_list = _BuiltinWrapper(list)
_tuple = _BuiltinWrapper(tuple)
_set = _BuiltinWrapper(set)
_sorted = _BuiltinWrapper(sorted)
_reversed = _BuiltinWrapper(reversed)
_sum = _BuiltinWrapper(sum)
_min = _BuiltinWrapper(min)
_max = _BuiltinWrapper(max)
_abs = _BuiltinWrapper(abs)
_type = _BuiltinWrapper(type)
_round = _BuiltinWrapper(round)
_repr = _BuiltinWrapper(repr)

_isinstance = _make_check(
    lambda types: lambda x: isinstance(x, types),
    "_isinstance({!r})"
)

_hasattr = _make_check(
    lambda name: lambda x: hasattr(x, name),
    "_hasattr({!r})"
)

_get = _make_check(
    lambda key, default=None: lambda x: x.get(key, default),
    "_get"
)

_getattr = _make_check(
    lambda name, default=None: lambda x: getattr(x, name, default),
    "_getattr"
)