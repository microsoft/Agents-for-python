import pytest
from typing import Optional, TypeVar, Union, Callable, Any

import aiohttp.web

from .application_runner import ApplicationRunner
from .environment import Environment
from .client import AgentClient, ResponseClient
from .sample import Sample

T = TypeVar("T", bound=type)
AppT = TypeVar("AppT", bound=aiohttp.web.Application) # for future extension w/ Union
    
def integration(
    service_url: Optional[str] = None,
    sample: Optional[type[Sample]] = None,
    environment: Optional[type[Environment]] = None,
    app: Optional[AppT] = None,
) -> Callable[[T], T]:
    """Factory function to create an Integration instance based on provided parameters.

    Essentially resolves to one of the static methods of Integration:
        `from_service_url`, `from_sample`, or `from_app`,
    based on the provided parameters.

    If a service URL is provided, it creates the Integration using that.
    If both sample and environment are provided, it creates the Integration using them.
    If an aiohttp application is provided, it creates the Integration using that.
    
    :param cls: The Integration class type.
    :param service_url: Optional service URL to connect to.
    :param sample: Optional Sample instance.
    :param environment: Optional Environment instance.
    :param host_agent: Flag to indicate if the agent should be hosted.
    :param app: Optional aiohttp application instance.
    :return: An instance of the Integration class.
    """

    def decorator(target_cls: T) -> T:

        if service_url:
            target_cls._service_url = service_url
        elif sample and environment:
            target_cls._sample_cls = sample
            target_cls._environment_cls = environment
        else:
            raise ValueError("Insufficient parameters to create Integration instance.")
        return target_cls
        
    return decorator