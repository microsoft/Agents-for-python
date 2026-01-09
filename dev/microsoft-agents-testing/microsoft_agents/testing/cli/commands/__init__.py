from click import Command

from .benchmark import benchmark
from .post import post
from .auth import auth

COMMAND_LIST: list[Command] = [
    benchmark,
    post,
    auth,
]

__all__ = [
    "COMMAND_LIST",
]
