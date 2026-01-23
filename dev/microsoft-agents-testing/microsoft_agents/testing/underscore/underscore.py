from __future__ import annotations
from typing import Any

from .models import (
    OperationType,
    PlaceholderInfo,
    PlaceholderType,
)

class ResolutionContext:
    """
    Context passed through the entire expression during resolution.
    
    This is the key to making indexed and named placeholders work - 
    everyone in the expression tree sees the same context with the
    same args and kwargs.
    """
    
    def __init__(self, args: tuple, kwargs: dict[str, Any]):
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
    def kwargs(self) -> dict[str, Any]:
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
        operations: list[tuple[OperationType, tuple, dict]] | None = None,
        placeholder_type: PlaceholderType = PlaceholderType.ANONYMOUS,
        placeholder_id: Any = None,  # index for INDEXED, name for NAMED
        bound_args: tuple = (),
        bound_kwargs: dict[str, Any] | None = None,
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
        operation: tuple[OperationType, tuple, dict] | None = None,
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