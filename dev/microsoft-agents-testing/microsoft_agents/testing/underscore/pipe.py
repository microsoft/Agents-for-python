from typing import Callable

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