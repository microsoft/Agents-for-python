from click import Command

from .benchmark import benchmark
from .ddt import ddt
from .post import post
from .auth import auth

COMMAND_LIST: list[Command] = [
    benchmark,
    ddt,
    post,
    auth,
]

__all__ = [
    "COMMAND_LIST",
]
