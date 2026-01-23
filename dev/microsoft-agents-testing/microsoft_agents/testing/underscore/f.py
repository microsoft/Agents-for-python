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
"""

from __future__ import annotations
from typing import Any, Callable, List, Tuple, Dict, Set, Optional
from enum import Enum, auto
from dataclasses import dataclass


class OperationType(Enum):
    """Types of operations in the chain."""
    BINARY_OP = auto()      # e.g., _ + 1, _ > 0
    UNARY_OP = auto()       # e.g., -_, abs(_)
    GETATTR = auto()        # e.g., _.foo
    GETITEM = auto()        # e.g., _[0]
    CALL = auto()           # e.g., _.method(arg1, arg2)
    RBINARY_OP = auto()     # e.g., 1 + _, 5 - _ (reverse binary ops)


class PlaceholderType(Enum):
    """Types of placeholder references."""
    ANONYMOUS = auto()      # _ - consumes next positional arg
    INDEXED = auto()        # _0, _1, _2 - refers to specific positional arg
    NAMED = auto()          # _var['name'] or _var.name - refers to named arg
    EXPR = auto()           # A sub-expression (used for composition)


@dataclass
class PlaceholderInfo:
    """Information about placeholders in an expression."""
    anonymous_count: int
    indexed: Set[int]
    named: Set[str]
    
    @property
    def total_positional_needed(self) -> int:
        """
        Minimum number of positional args needed.
        
        This is the max of:
        - The number of anonymous placeholders
        - The highest indexed placeholder + 1
        """
        max_indexed = max(self.indexed) + 1 if self.indexed else 0
        return max(self.anonymous_count, max_indexed)
    
    def __repr__(self) -> str:
        parts = []
        if self.anonymous_count:
            parts.append(f"anonymous={self.anonymous_count}")
        if self.indexed:
            parts.append(f"indexed={self.indexed}")
        if self.named:
            parts.append(f"named={self.named}")
        return f"PlaceholderInfo({', '.join(parts)})"


class ResolutionContext:
    """
    Context passed through the entire expression during resolution.
    
    This is the key to making indexed and named placeholders work - 
    everyone in the expression tree sees the same context with the
    same args and kwargs.
    """
    
    def __init__(self, args: tuple, kwargs: Dict[str, Any]):
        self._args = args
        self._kwargs = kwargs
        self._next_anonymous_index = 0
        self._max_index_requested = -1
    
    def consume_anonymous(self) -> Any:
        """Consume and return the next anonymous positional argument."""
        if self._next_anonymous_index >= len(self._args):
            raise _NotEnoughArgs(
                needed=self._next_anonymous_index + 1,
                provided=len(self._args)
            )
        value = self._args[self._next_anonymous_index]
        self._next_anonymous_index += 1
        return value
    
    def get_indexed(self, index: int) -> Any:
        """Get a specific positional argument by index."""
        if index >= len(self._args):
            raise _NotEnoughArgs(
                needed=index + 1,
                provided=len(self._args)
            )
        self._max_index_requested = max(self._max_index_requested, index)
        return self._args[index]
    
    def get_named(self, name: str) -> Any:
        """Get a named argument from kwargs."""
        if name not in self._kwargs:
            raise _MissingNamedArg(name)
        return self._kwargs[name]
    
    @property
    def args(self) -> tuple:
        return self._args
    
    @property
    def kwargs(self) -> Dict[str, Any]:
        return self._kwargs


class _NotEnoughArgs(Exception):
    """Signal that we need more positional arguments."""
    def __init__(self, needed: int, provided: int):
        self.needed = needed
        self.provided = provided
        super().__init__(f"Need {needed} args, got {provided}")


class _MissingNamedArg(Exception):
    """Signal that a named argument is missing."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Missing named argument: {name}")


class Underscore:
    """
    A placeholder object that builds up a chain of deferred operations.
    
    Each operation on an Underscore returns a NEW Underscore with the
    operation added to its chain. When called with arguments, it applies
    all operations using a shared resolution context.
    """
    
    _INTERNAL_ATTRS = frozenset({
        '_operations', '_placeholder_type', '_placeholder_id', '_bound_args',
        '_bound_kwargs', '_inner_expr', '_resolve', '_resolve_in_context', 
        '_copy_with', '_is_compound', '__class__', '__dict__',
    })
    
    def __init__(
        self, 
        operations: List[Tuple[OperationType, tuple, dict]] | None = None,
        placeholder_type: PlaceholderType = PlaceholderType.ANONYMOUS,
        placeholder_id: Any = None,  # index for INDEXED, name for NAMED
        bound_args: tuple = (),
        bound_kwargs: Dict[str, Any] | None = None,
        inner_expr: 'Underscore | None' = None,  # For EXPR type
    ):
        """
        Initialize an Underscore placeholder.
        
        Args:
            operations: Chain of deferred operations.
            placeholder_type: How this placeholder gets its base value.
            placeholder_id: The index (for INDEXED) or name (for NAMED).
            bound_args: Partially applied positional arguments.
            bound_kwargs: Partially applied keyword arguments.
            inner_expr: For EXPR type, the inner expression to resolve first.
        """
        object.__setattr__(self, '_operations', operations or [])
        object.__setattr__(self, '_placeholder_type', placeholder_type)
        object.__setattr__(self, '_placeholder_id', placeholder_id)
        object.__setattr__(self, '_bound_args', bound_args)
        object.__setattr__(self, '_bound_kwargs', bound_kwargs or {})
        object.__setattr__(self, '_inner_expr', inner_expr)
    
    @property
    def _is_compound(self) -> bool:
        """
        Check if this is a compound expression that should be isolated
        when used in further operations.
        
        An expression is compound if it has operations or bound args,
        meaning it's not just a simple placeholder reference.
        """
        return bool(self._operations) or bool(self._bound_args) or bool(self._bound_kwargs)
    
    def _wrap_if_compound(self) -> Underscore:
        """
        If this is a compound expression, wrap it as an EXPR placeholder.
        
        This ensures that when we add operations to it, the original
        expression is treated as an atomic unit.
        """
        if self._is_compound:
            return Underscore(
                placeholder_type=PlaceholderType.EXPR,
                inner_expr=self,
            )
        return self
    
    def _copy_with(
        self, 
        operation: Tuple[OperationType, tuple, dict] | None = None,
        **overrides
    ) -> Underscore:
        """Create a new Underscore, optionally with an additional operation."""
        new_ops = self._operations.copy()
        if operation:
            new_ops.append(operation)
        
        return Underscore(
            operations=overrides.get('operations', new_ops),
            placeholder_type=overrides.get('placeholder_type', self._placeholder_type),
            placeholder_id=overrides.get('placeholder_id', self._placeholder_id),
            bound_args=overrides.get('bound_args', self._bound_args),
            bound_kwargs=overrides.get('bound_kwargs', self._bound_kwargs),
            inner_expr=overrides.get('inner_expr', self._inner_expr),
        )
    
    def _resolve_value(self, value: Any, ctx: ResolutionContext) -> Any:
        """
        Resolve a value within the current context.
        
        If the value is an Underscore, resolve it using the shared context.
        Otherwise, return it as-is.
        """
        if isinstance(value, Underscore):
            return value._resolve_in_context(ctx)
        return value
    
    def _resolve_in_context(self, ctx: ResolutionContext) -> Any:
        """
        Resolve this placeholder using the given context.
        
        This is the core resolution logic. It:
        1. Gets the base value (from anonymous, indexed, named, or expr source)
        2. Applies each operation in the chain
        """
        # Step 1: Get the base value based on placeholder type
        if self._placeholder_type == PlaceholderType.ANONYMOUS:
            result = ctx.consume_anonymous()
        elif self._placeholder_type == PlaceholderType.INDEXED:
            result = ctx.get_indexed(self._placeholder_id)
        elif self._placeholder_type == PlaceholderType.NAMED:
            result = ctx.get_named(self._placeholder_id)
        elif self._placeholder_type == PlaceholderType.EXPR:
            # Resolve the inner expression first
            result = self._inner_expr._resolve_in_context(ctx)
        else:
            raise ValueError(f"Unknown placeholder type: {self._placeholder_type}")
        
        # Step 2: Apply each operation in the chain
        for op_type, args, kwargs in self._operations:
            if op_type == OperationType.BINARY_OP:
                op_name, other = args[0], args[1]
                other = self._resolve_value(other, ctx)
                op_func = getattr(result, op_name)
                result = op_func(other)
                
            elif op_type == OperationType.RBINARY_OP:
                op_name, other = args[0], args[1]
                other = self._resolve_value(other, ctx)
                op_func = getattr(other, op_name)
                result = op_func(result)
                
            elif op_type == OperationType.UNARY_OP:
                op_name = args[0]
                op_func = getattr(result, op_name)
                result = op_func()
                
            elif op_type == OperationType.GETATTR:
                attr_name = args[0]
                result = getattr(result, attr_name)
                
            elif op_type == OperationType.GETITEM:
                key = args[0]
                key = self._resolve_value(key, ctx)
                result = result[key]
                
            elif op_type == OperationType.CALL:
                resolved_args = tuple(
                    self._resolve_value(a, ctx) for a in args
                )
                resolved_kwargs = {
                    k: self._resolve_value(v, ctx)
                    for k, v in kwargs.items()
                }
                result = result(*resolved_args, **resolved_kwargs)
        
        return result
    
    def __call__(self, *args, **kwargs) -> Any:
        """
        Either resolve the placeholder, return a partial, or record a method call.
        """
        # Check if we should interpret this as a method call
        if (self._operations and 
            self._operations[-1][0] == OperationType.GETATTR):
            # Convert the trailing getattr into a call
            new_ops = self._operations[:-1]
            attr_name = self._operations[-1][1][0]
            new_ops.append((OperationType.GETATTR, (attr_name,), {}))
            new_ops.append((OperationType.CALL, args, kwargs))
            return self._copy_with(operations=new_ops)
        
        # Combine bound args/kwargs with new ones
        all_args = self._bound_args + args
        all_kwargs = {**self._bound_kwargs, **kwargs}
        
        if not all_args and not all_kwargs:
            raise TypeError("Resolving placeholder requires at least one argument")
        
        # Try to resolve
        ctx = ResolutionContext(all_args, all_kwargs)
        
        try:
            return self._resolve_in_context(ctx)
        except (_NotEnoughArgs, _MissingNamedArg):
            # Not enough arguments - return a partial
            return self._copy_with(
                bound_args=all_args,
                bound_kwargs=all_kwargs,
            )
    
    def __getattr__(self, name: str) -> Underscore:
        """Record attribute access as a deferred operation."""
        # Wrap compound expressions to preserve grouping
        wrapped = self._wrap_if_compound()
        return wrapped._copy_with((OperationType.GETATTR, (name,), {}))
    
    def __getitem__(self, key: Any) -> Underscore:
        """
        Record item access as a deferred operation.
        
        _[0] gets item at index 0 from the resolved value.
        _["key"] gets item with key "key" from the resolved value.
        
        To create placeholders, use _var[0] or _var["name"] instead.
        """
        # Wrap compound expressions to preserve grouping
        wrapped = self._wrap_if_compound()
        return wrapped._copy_with((OperationType.GETITEM, (key,), {}))
    
    def __repr__(self) -> str:
        """Provide a readable representation of the placeholder."""
        # Base placeholder representation
        if self._placeholder_type == PlaceholderType.ANONYMOUS:
            base = "_"
        elif self._placeholder_type == PlaceholderType.INDEXED:
            base = f"_{self._placeholder_id}"
        elif self._placeholder_type == PlaceholderType.NAMED:
            base = f"_var[{self._placeholder_id!r}]"
        elif self._placeholder_type == PlaceholderType.EXPR:
            base = f"({self._inner_expr!r})"
        else:
            base = "_"
        
        if not self._operations and not self._bound_args and not self._bound_kwargs:
            return base
        
        parts = [base]
        for op_type, args, kwargs in self._operations:
            if op_type == OperationType.BINARY_OP:
                op_symbol = _OP_SYMBOLS.get(args[0], args[0])
                other = args[1]
                other_repr = repr(other)
                parts.append(f" {op_symbol} {other_repr}")
            elif op_type == OperationType.RBINARY_OP:
                op_symbol = _OP_SYMBOLS.get(args[0], args[0])
                other = args[1]
                other_repr = repr(other)
                parts.insert(0, f"{other_repr} {op_symbol} ")
            elif op_type == OperationType.UNARY_OP:
                op_symbol = _OP_SYMBOLS.get(args[0], args[0])
                parts.insert(0, op_symbol)
            elif op_type == OperationType.GETATTR:
                parts.append(f".{args[0]}")
            elif op_type == OperationType.GETITEM:
                key = args[0]
                key_repr = repr(key)
                parts.append(f"[{key_repr}]")
            elif op_type == OperationType.CALL:
                arg_strs = [repr(a) for a in args]
                arg_strs += [f"{k}={repr(v)}" for k, v in kwargs.items()]
                parts.append(f"({', '.join(arg_strs)})")
        
        result = "".join(parts)
        
        # Show bound args if any
        if self._bound_args or self._bound_kwargs:
            bound_parts = [repr(a) for a in self._bound_args]
            bound_parts += [f"{k}={v!r}" for k, v in self._bound_kwargs.items()]
            result = f"({result}).partial({', '.join(bound_parts)})"
        
        return result


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


# =============================================================================
# Introspection Functions
# =============================================================================

def _collect_placeholders(expr: Any, info: PlaceholderInfo) -> None:
    """
    Recursively collect placeholder information from an expression.
    
    This walks the entire expression tree and records all placeholders found.
    """
    if not isinstance(expr, Underscore):
        return
    
    # Record this placeholder's type
    if expr._placeholder_type == PlaceholderType.ANONYMOUS:
        info.anonymous_count += 1
    elif expr._placeholder_type == PlaceholderType.INDEXED:
        info.indexed.add(expr._placeholder_id)
    elif expr._placeholder_type == PlaceholderType.NAMED:
        info.named.add(expr._placeholder_id)
    elif expr._placeholder_type == PlaceholderType.EXPR:
        # Recurse into inner expression
        _collect_placeholders(expr._inner_expr, info)
    
    # Check all operations for nested Underscores
    for op_type, args, kwargs in expr._operations:
        for arg in args:
            _collect_placeholders(arg, info)
        for value in kwargs.values():
            _collect_placeholders(value, info)


def get_placeholder_info(expr: Underscore) -> PlaceholderInfo:
    """
    Get complete information about all placeholders in an expression.
    
    Args:
        expr: An Underscore expression to analyze.
        
    Returns:
        PlaceholderInfo with counts and sets of all placeholder types.
        
    Example:
        >>> expr = _0 + _1 * _var["scale"] + _
        >>> info = get_placeholder_info(expr)
        >>> info.anonymous_count
        1
        >>> info.indexed
        {0, 1}
        >>> info.named
        {'scale'}
        >>> info.total_positional_needed
        2
    """
    info = PlaceholderInfo(anonymous_count=0, indexed=set(), named=set())
    _collect_placeholders(expr, info)
    return info


def get_anonymous_count(expr: Underscore) -> int:
    """
    Count the number of anonymous placeholders (_) in an expression.
    
    Example:
        >>> get_anonymous_count(_ + _ * _)
        3
        >>> get_anonymous_count(_0 + _1)
        0
    """
    return get_placeholder_info(expr).anonymous_count


def get_indexed_placeholders(expr: Underscore) -> Set[int]:
    """
    Get the set of indexed placeholder positions used in an expression.
    
    Example:
        >>> get_indexed_placeholders(_0 + _1 * _0)
        {0, 1}
        >>> get_indexed_placeholders(_ + _)
        set()
    """
    return get_placeholder_info(expr).indexed


def get_named_placeholders(expr: Underscore) -> Set[str]:
    """
    Get the set of named placeholders used in an expression.
    
    Example:
        >>> get_named_placeholders(_var["x"] + _var["y"] * _var["x"])
        {'x', 'y'}
        >>> get_named_placeholders(_ + _0)
        set()
    """
    return get_placeholder_info(expr).named


def get_required_args(expr: Underscore) -> Tuple[int, Set[str]]:
    """
    Get the minimum positional args and required named args for an expression.
    
    Returns:
        A tuple of (min_positional_count, set_of_required_names).
        
    Example:
        >>> pos, named = get_required_args(_0 + _1 * _var["scale"])
        >>> pos
        2
        >>> named
        {'scale'}
    """
    info = get_placeholder_info(expr)
    return info.total_positional_needed, info.named


def is_placeholder(value: Any) -> bool:
    """Check if a value is an Underscore placeholder."""
    return isinstance(value, Underscore)


# =============================================================================
# Operator Definitions
# =============================================================================

def _make_binop(op_name: str):
    """Factory for binary operator methods."""
    def method(self: Underscore, other: Any) -> Underscore:
        # Wrap compound expressions to preserve grouping
        wrapped = self._wrap_if_compound()
        return wrapped._copy_with((OperationType.BINARY_OP, (op_name, other), {}))
    return method


def _make_rbinop(op_name: str):
    """Factory for reverse binary operator methods."""
    def method(self: Underscore, other: Any) -> Underscore:
        # Wrap compound expressions to preserve grouping
        wrapped = self._wrap_if_compound()
        return wrapped._copy_with((OperationType.RBINARY_OP, (op_name, other), {}))
    return method


def _make_unop(op_name: str):
    """Factory for unary operator methods."""
    def method(self: Underscore) -> Underscore:
        # Wrap compound expressions to preserve grouping
        wrapped = self._wrap_if_compound()
        return wrapped._copy_with((OperationType.UNARY_OP, (op_name,), {}))
    return method


_OP_SYMBOLS = {
    '__add__': '+',
    '__sub__': '-',
    '__mul__': '*',
    '__truediv__': '/',
    '__floordiv__': '//',
    '__mod__': '%',
    '__pow__': '**',
    '__eq__': '==',
    '__ne__': '!=',
    '__lt__': '<',
    '__le__': '<=',
    '__gt__': '>',
    '__ge__': '>=',
    '__and__': '&',
    '__or__': '|',
    '__xor__': '^',
    '__lshift__': '<<',
    '__rshift__': '>>',
    '__neg__': '-',
    '__pos__': '+',
    '__invert__': '~',
}


# =============================================================================
# Attach operators to the Underscore class
# =============================================================================

# Comparison operators
Underscore.__lt__ = _make_binop('__lt__')
Underscore.__le__ = _make_binop('__le__')
Underscore.__gt__ = _make_binop('__gt__')
Underscore.__ge__ = _make_binop('__ge__')
Underscore.__eq__ = _make_binop('__eq__')  # type: ignore
Underscore.__ne__ = _make_binop('__ne__')  # type: ignore

# Arithmetic operators
Underscore.__add__ = _make_binop('__add__')
Underscore.__sub__ = _make_binop('__sub__')
Underscore.__mul__ = _make_binop('__mul__')
Underscore.__truediv__ = _make_binop('__truediv__')
Underscore.__floordiv__ = _make_binop('__floordiv__')
Underscore.__mod__ = _make_binop('__mod__')
Underscore.__pow__ = _make_binop('__pow__')

# Reverse arithmetic
Underscore.__radd__ = _make_rbinop('__add__')
Underscore.__rsub__ = _make_rbinop('__sub__')
Underscore.__rmul__ = _make_rbinop('__mul__')
Underscore.__rtruediv__ = _make_rbinop('__truediv__')
Underscore.__rfloordiv__ = _make_rbinop('__floordiv__')
Underscore.__rmod__ = _make_rbinop('__mod__')
Underscore.__rpow__ = _make_rbinop('__pow__')

# Bitwise operators
Underscore.__and__ = _make_binop('__and__')
Underscore.__or__ = _make_binop('__or__')
Underscore.__xor__ = _make_binop('__xor__')
Underscore.__lshift__ = _make_binop('__lshift__')
Underscore.__rshift__ = _make_binop('__rshift__')

# Reverse bitwise
Underscore.__rand__ = _make_rbinop('__and__')
Underscore.__ror__ = _make_rbinop('__or__')
Underscore.__rxor__ = _make_rbinop('__xor__')
Underscore.__rlshift__ = _make_rbinop('__lshift__')
Underscore.__rrshift__ = _make_rbinop('__rshift__')

# Unary operators
Underscore.__neg__ = _make_unop('__neg__')
Underscore.__pos__ = _make_unop('__pos__')
Underscore.__invert__ = _make_unop('__invert__')


# =============================================================================
# Placeholder instances
# =============================================================================

# Anonymous placeholder - consumes args in order
_ = Underscore()

# Indexed placeholders - refer to specific positional args
_0 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=0)
_1 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=1)
_2 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=2)
_3 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=3)
_4 = Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=4)

# Factory for creating placeholders dynamically
_var = _VarFactory()


def _n(index: int) -> Underscore:
    """Create an indexed placeholder for any position."""
    return Underscore(placeholder_type=PlaceholderType.INDEXED, placeholder_id=index)


# =============================================================================
# Helper for functional composition
# =============================================================================

def pipe(*funcs: Callable) -> Callable:
    """
    Compose functions left-to-right (pipeline style).
    
    Example:
        >>> process = pipe(_ + 1, _ * 2, str)
        >>> process(5)  # (5 + 1) * 2 = 12, then str -> "12"
    """
    def composed(value):
        for f in funcs:
            value = f(value)
        return value
    return composed