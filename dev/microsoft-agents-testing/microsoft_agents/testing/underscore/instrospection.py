from typing import Any, Set, Tuple

from .underscore import (
    PlaceholderInfo,
    PlaceholderType,
    Underscore,
)

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