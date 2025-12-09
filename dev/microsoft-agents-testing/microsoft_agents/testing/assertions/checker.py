from typing import Protocol, TypeVar, overload, Iterable, Callable
from pydantic import BaseModel

from .assertions import Assertions

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)

def create_base(model: dict | BaseModel | Callable | None = None, **kwargs) -> dict:
    if model is None:
        return {**kwargs}
    elif isinstance(model, dict):
        return dict(Assertions.expand(model), **kwargs)
    elif isinstance(model, BaseModel):
        return {
            **model.model_dump(exclude_unset=True),
            **kwargs
        }
    elif isinstance(model, Callable):
        return {
            "__callable": model,
            **kwargs
        }
    else:
        raise TypeError("model must be a dict, BaseModel, or Callable")

class Checker:

    def __init__(self, _selector: dict | BaseModel | Callable | None = None, **kwargs):
        self._selector = create_base(_selector, **kwargs)

    def check(self, actual: dict | BaseModel) -> bool:
        return Assertions.evaluate(actual, self._selector)

    def __call__(self, actual: dict | BaseModel) -> bool:
        return self.check(actual)

    @overload
    def select(self, lst: list[dict]) -> list[dict]: ...
    @overload
    def select(self, lst: list[BaseModelT]) -> list[BaseModelT]: ...
    def select(self, lst: list[dict] | list[BaseModelT]) -> list[dict] | list[BaseModelT]:
        res = []
        for item in lst:
            if self.check(item):
                res.append(item)
        return res
    
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
        last = None
        for item in lst:
            if self.check(item):
                last = item
        return last