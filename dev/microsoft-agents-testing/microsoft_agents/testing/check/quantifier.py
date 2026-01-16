from typing import Protocol

class Quantifier(Protocol):
    
    @staticmethod
    def __call__(items: list[bool]) -> bool:
        ...

def for_all(items: list[bool]) -> bool:
    return all(items)

def for_any(items: list[bool]) -> bool:
    return any(items)

def for_none(items: list[bool]) -> bool:
    return all(not item for item in items)

def for_one(items: list[bool]) -> bool:
    return sum(1 for item in items if item) == 1

def for_n(n: int) -> Quantifier:
    def _for_n(items: list[bool]) -> bool:
        return sum(1 for item in items if item) == n
    return _for_n