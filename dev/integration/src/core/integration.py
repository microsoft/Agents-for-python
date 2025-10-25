from random import sample
import pytest

from typing import Optional, TypeVar, Union

import aiohttp.web

from .runner import AppRunner
from .environment import Environment
from .response_server import ResponseServer
from .sample import Sample

T = TypeVar("T", bound=type)
AppT = TypeVar("AppT", bound=aiohttp.web.Application) # for future extension w/ Union

async def start_response_server():
    pass

class Integration:

    @staticmethod
    def _with_response_server(target_cls: T, host_response: bool) -> T:
        """Wraps the target class to include a response server if needed."""

        _prev_setup_method = getattr(target_cls, "setup_method", None)
        _prev_teardown_method = getattr(target_cls, "teardown_method", None)

        async def setup_method(self):
            if host_response:
                self._response_server = ResponseServer()
                await self._response_server.__aenter__()
            if _prev_setup_method:
                await _prev_setup_method(self)

        async def teardown_method(self):
            if host_response:
                await self._response_server.__aexit__(None, None, None)
            if _prev_teardown_method:
                await _prev_teardown_method(self)

        target_cls.setup_method = setup_method
        target_cls.teardown_method = teardown_method

        return target_cls

    @staticmethod
    def from_service_url(target_cls: T, service_url: str, host_response: bool = False) -> T:
        """Creates an Integration instance using a service URL."""

        async def setup_method(self):
            self._service_url = service_url

        async def teardown_method(self):
            self._service_url = service_url

        target_cls.setup_method = setup_method
        target_cls.teardown_method = teardown_method

        target_cls = Integration._with_response_server(target_cls, host_response)

        return target_cls
    
    @staticmethod
    def from_sample(
        target_cls: T,
        sample_cls: type[Sample],
        environment_cls: type[Environment],
        host_agent: bool = False,
        host_response: bool = False
    ) -> T:
        """Creates an Integration instance using a sample and environment."""

        def setup_method(self):
            self._environment = environment_cls(sample_cls.get_config())
            await self._environment.__aenter__()

            self._sample = sample_cls(self._environment)
            await self._sample.__aenter__()

        def teardown_method(self):
            await self._sample.__aexit__(None, None, None)
            await self._environment.__aexit__(None, None, None)

        target_cls = Integration._with_response_server(target_cls, host_response)

        return target_cls
    
    @staticmethod
    def from_app(target_cls: T, app: AppT, host_response: bool = True) -> T:
        """Creates an Integration instance using an aiohttp application."""

        async def setup_method(self):

            self._app = app
            self._runner = AppRunner(self._app)
            await self._runner.__aenter__()

        async def teardown_method(self):
            await self._runner.__aexit__(None, None, None)

        target_cls = Integration._with_response_server(target_cls, host_response)

        return target_cls
    
def integration(
    cls: T,
    service_url: Optional[str] = None,
    sample_cls: Optional[type[Sample]] = None,
    environment_cls: Optional[type[Environment]] = None,
    app: Optional[AppT] = None,
    host_agent: bool = False,
    host_response: bool = True,
) -> T:
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
    
    if service_url:
        return Integration.from_service_url(cls, service_url, host_response=host_response)
    elif sample_cls and environment_cls:
        return Integration.from_sample(cls, sample_cls, environment_cls, host_agent=host_agent, host_response=host_response)
    elif app:
        return Integration.from_app(cls, app, host_response=host_response)
    else:
        raise ValueError("Insufficient parameters to create Integration instance.")