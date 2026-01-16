from typing import TypeVar, Iterable, Protocol, Callable

S = TypeVar("S")

class Quantifier(Protocol[S]):
    def __call__(self, items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
        ... 

def for_all(items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
    return all(predicate(item) for item in items)

def for_any(items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
    return any(predicate(item) for item in items)

def for_none(items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
    return all(not predicate(item) for item in items)

def for_exactly(n: int) -> Quantifier[S]:
    def quantifier(items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
        return sum(1 for item in items if predicate(item)) == n
    return quantifier

def for_one(items: Iterable[S], predicate: Callable[[S], bool]) -> bool:
    return for_exactly(1)(items, predicate)