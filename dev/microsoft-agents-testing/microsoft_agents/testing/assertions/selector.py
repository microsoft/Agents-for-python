from typing import Protocol, TypeVar, overload, Iterable
from pydantic import BaseModel

from .engine import evaluate, expand
from .unset import Unset

class Predicate(Protocol):
    def __call__(self, item: dict) -> bool:
        ...

BaseModelT = TypeVar("BaseModelT", bound=BaseModelT)

class Selector:

    def __init__(self, _selector: dict | Predicate | None = None, **kwargs):

        if _selector is None:
            _selector = {**kwargs}
        elif isinstance(_selector, dict):
            _selector = dict(expand(_selector), **kwargs)
        else:
            _selector = {
                "__predicate": _selector,
                **kwargs
            }

        self._selector = _selector

    def check(self, actual: dict | BaseModelT) -> bool:
        return evaluate(actual, self._selector)

    def __call__(self, actual: dict | BaseModelT) -> bool:
        return self.check(actual)

    @overload
    def select(self, lst: list[dict]) -> list[dict]: ...
    @overload
    def select(self, lst: list[BaseModelT]) -> list[BaseModelT]: ...
    def select(self, lst: list[dict] | list[BaseModelT]) -> list[dict] | list[BaseModelT]:
        return [item for item in lst if self.check(item)]
    
    @overload
    def first(self, lst: Iterable[dict]) -> dict | None: ...
    @overload
    def first(self, lst: Iterable[BaseModelT]) -> BaseModelT | None: ...
    def first(self, lst: Iterable[dict] | Iterable[BaseModelT]) -> dict | BaseModelT | None:
        for item in lst:
            if self.check(item):
                return item
        return None
    
    @overload
    def last(self, lst: Iterable[dict]) -> dict | None: ...
    @overload
    def last(self, lst: Iterable[BaseModelT]) -> BaseModelT | None: ...
    def last(self, lst: Iterable[dict] | Iterable[BaseModelT]) -> dict | BaseModelT | None:
        return self.first(reversed(lst))
    
