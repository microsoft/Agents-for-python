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
    APPLY_BUILTIN = auto()  # e.g., _len(_), _str(_)


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
    indexed: set[int]
    named: set[str]
    
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