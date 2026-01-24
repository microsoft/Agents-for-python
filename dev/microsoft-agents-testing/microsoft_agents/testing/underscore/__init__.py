"""
Underscore Placeholder Implementation
======================================

A modern, lightweight implementation of a placeholder object for building
deferred function expressions. Inspired by fn.py's underscore but with its 
own design choices.

Usage Examples:
    >>> from microsoft_agents.testing.check.engine.underscore.f import _, _0, _1, _2, _var
    
    # Basic arithmetic - single argument
    >>> add_one = _ + 1
    >>> add_one(5)  # Returns 6
    
    # Multiple placeholders - each _ consumes the next argument
    >>> add = _ + _
    >>> add(2, 5)  # Returns 7
    
    # Indexed placeholders - reuse the same argument
    >>> square = _0 * _0
    >>> square(5)  # Returns 25
    
    # Create placeholders dynamically with _var
    >>> _var[0] * _var[0]   # Same as _0 * _0
    >>> _var["name"]        # Named placeholder
    >>> _var.x              # Also creates named placeholder "x"
    
    # Item access on results (not placeholder creation)
    >>> get_first = _[0]
    >>> get_first([1, 2, 3])  # Returns 1
    
    >>> get_key = _["key"]
    >>> get_key({"key": "value"})  # Returns "value"
    
    # Mixed indexed placeholders
    >>> expr = _0 + _1 * _0
    >>> expr(2, 3)  # Returns 2 + 3 * 2 = 8
    
    # Partial application - provide fewer args than needed
    >>> add = _ + _
    >>> add2 = add(2)   # Returns a partial, waiting for one more arg
    >>> add2(5)         # Returns 7
    
    # Composing partials preserves grouping
    >>> f = _0 + _0 - _1
    >>> g = f(2) * -1   # This is (_0 + _0 - _1) * -1, not _0 + _0 - _1 * -1
    >>> g(3)            # Returns (2 + 2 - 3) * -1 = -1
    
    # Named placeholders via _var
    >>> greet = "Hello, " + _var["name"]
    >>> greet(name="World")  # Returns "Hello, World"
    
    # Or using attribute syntax
    >>> greet = "Hello, " + _var.name
    >>> greet(name="World")  # Returns "Hello, World"
    
    # Introspect placeholders in an expression
    >>> expr = _0 + _1 * _var["scale"]
    >>> get_indexed_placeholders(expr)   # Returns {0, 1}
    >>> get_named_placeholders(expr)     # Returns {'scale'}
    >>> get_anonymous_count(expr)        # Returns 0
    
    # Comparisons  
    >>> is_positive = _ > 0
    >>> is_positive(5)  # Returns True
    
    # Method chaining
    >>> get_upper = _.upper()
    >>> get_upper("hello")  # Returns "HELLO"
    
    # Complex multi-argument expressions
    >>> expr = (_ + _) * _
    >>> expr(1, 2, 3)  # Returns (1 + 2) * 3 = 9

Design Choices:
---------------
1. IMMUTABILITY: Each operation returns a NEW Underscore instance. The original
   placeholder is never mutated. This makes it safe to reuse and compose.

2. OPERATION CHAIN: Operations are stored as a list of (operation_type, args, kwargs)
   tuples. This is simpler than building an AST and sufficient for most use cases.
   
3. RESOLUTION CONTEXT: A context object is passed through the entire expression
   during resolution, tracking consumed positional args and providing access to
   all args/kwargs. This enables indexed (_0, _1) and named placeholders.

4. POSITIONAL PLACEHOLDERS: Each bare `_` in an expression consumes the next 
   positional argument. Indexed `_0`, `_1`, etc. refer to specific positions.

5. AUTOMATIC PARTIAL APPLICATION: If you provide fewer arguments than there are
   placeholders, you get back a new Underscore with those args "baked in".

6. EXPRESSION ISOLATION: When composing expressions (e.g., `f(2) * -1`), the
   original expression is treated as an atomic unit, preserving grouping.

7. ATTRIBUTE vs METHOD: `_.foo` returns a new placeholder that will access `.foo`.
   `_.foo()` returns one that will call `.foo()`. These are distinct operations.

8. _var FOR PLACEHOLDER CREATION: Use `_var[0]`, `_var["name"]`, or `_var.name`
   to create placeholders. `_[0]` and `_["key"]` are item access operations.

Possible Extensions:
--------------------
- Short-circuit evaluation for boolean operations  
- Debug/trace mode to see the operation chain
- Async method support
- global vs local context for named and indexed placeholders
"""

from .instrospection import (
    get_placeholder_info,
    get_anonymous_count,
    get_indexed_placeholders,
    get_named_placeholders,
    get_required_args,
    is_placeholder,
)

from .pipe import pipe

from .shortcuts import (
    _, _0, _1, _2, _3, _4, _n, _var,
)

from .underscore import (
    Underscore,
    PlaceholderInfo,
)

from .builtin_wrappers import (
      _len,
      _str,
      _int,
      _float,
      _bool,
      _list,
      _tuple,
      _set,
      _sorted,
      _reversed,
      _sum,
      _min,
      _max,
      _abs,
      _type,
)

__all__ = [
    "_", "_0", "_1", "_2", "_3", "_4", "_n", "_var",
    "Underscore",
    "PlaceholderInfo",
    "pipe",
    "get_placeholder_info",
    "get_anonymous_count",
    "get_indexed_placeholders", 
    "get_named_placeholders",
    "get_required_args",
    "is_placeholder",

    "_len",
    "_str",
   "_int",
   "_float",
   "_bool",
   "_list",
   "_tuple",
   "_set",
   "_sorted",
   "_reversed",
   "_sum",
   "_min",
   "_max",
   "_abs",
   "_type",
]