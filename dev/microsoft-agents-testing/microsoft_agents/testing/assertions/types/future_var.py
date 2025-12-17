from typing import Callable

class FutureVar:
    """A class representing a future variable for deferred evaluation in assertions."""

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other) -> Callable[..., bool]:
        return lambda ctx: ctx.get(self.name) == other
    
    def __ne__(self, other) -> Callable[..., bool]:
        return lambda ctx: ctx.get(self.name) != other
    
    def __lt__(self, other) -> Callable[..., bool]:
        return lambda ctx: ctx.get(self.name) < other
    
    def __le__(self, other) -> Callable[..., bool]:
        return lambda ctx: ctx.get(self.name) <= other
    
    def __gt__(self, other) -> Callable[..., bool]:
        return lambda ctx: ctx.get(self.name) > other
    
    def __ge__(self, other) -> Callable[..., bool]:    
        return lambda ctx: ctx.get(self.name) >= other
    
    def __contains__(self, item) -> Callable[..., bool]:
        return lambda ctx: item in ctx.get(self.name, "")
    
    def __str__(self) -> str:
        return f"FutureVar(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()