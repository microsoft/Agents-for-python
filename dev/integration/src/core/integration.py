from typing import Optional, TypeVar, Union, Callable, Any

import aiohttp.web

from .application_runner import ApplicationRunner
from .environment import Environment
from .client import AgentClient, ResponseClient
from .sample import Sample

T = TypeVar("T", bound=type)
AppT = TypeVar("AppT", bound=aiohttp.web.Application) # for future extension w/ Union

class _Integration:

    @staticmethod
    def _with_response_client(target_cls: T, host_response: bool) -> T:
        """Wraps the target class to include a response client if needed."""

        _prev_setup_method = getattr(target_cls, "setup_method", None)
        _prev_teardown_method = getattr(target_cls, "teardown_method", None)

        async def setup_method(self):
            if host_response:
                self._response_client = ResponseClient()
                await self._response_client.__aenter__()
            if _prev_setup_method:
                await _prev_setup_method(self)

        async def teardown_method(self):
            if host_response:
                await self._response_client.__aexit__(None, None, None)
            if _prev_teardown_method:
                await _prev_teardown_method(self)

        target_cls.setup_method = setup_method
        target_cls.teardown_method = teardown_method

        return target_cls

    @staticmethod
    def from_service_url(service_url: str, host_response: bool = False) -> Callable[[T], T]:
        """Creates an Integration instance using a service URL."""

        def decorator(target_cls: T) -> T:

            async def setup_method(self):
                self._service_url = service_url

            async def teardown_method(self):
                self._service_url = service_url

            target_cls.setup_method = setup_method
            target_cls.teardown_method = teardown_method

            target_cls = _Integration._with_response_client(target_cls, host_response)

            return target_cls
        
        return decorator
    
    @staticmethod
    def from_sample(
        sample_cls: type[Sample],
        environment_cls: type[Environment],
        host_agent: bool = False,
        host_response: bool = False
    ) -> Callable[[T], T]:
        """Creates an Integration instance using a sample and environment."""

        def decorator(target_cls: T) -> T:

            async def setup_method(self):
                self._environment = environment_cls(sample_cls.get_config())
                await self._environment.__aenter__()

                self._sample = sample_cls(self._environment)
                await self._sample.__aenter__()

            async def teardown_method(self):
                await self._sample.__aexit__(None, None, None)
                await self._environment.__aexit__(None, None, None)

            target_cls = _Integration._with_response_client(target_cls, host_response)

            return target_cls
        
        return decorator
    
    # not supported yet
    # @staticmethod
    # def from_app(app: Any, host_response: bool = True) -> Callable[[T], T]:
    #     """Creates an Integration instance using an aiohttp application."""

    #     def decorator(target_cls: T) -> T:

    #         async def setup_method(self):

    #             self._app = app

    #             self._runner = self._environment.create_runner()
    #             await self._runner.__aenter__()

    #         async def teardown_method(self):
    #             await self._runner.__aexit__(None, None, None)

    #         target_cls = _Integration._with_response_client(target_cls, host_response)

    #         return target_cls
        
    #     return decorator
    
def integration(
    service_url: Optional[str] = None,
    sample: Optional[type[Sample]] = None,
    environment: Optional[type[Environment]] = None,
    app: Optional[AppT] = None,
    host_agent: bool = False,
    host_response: bool = True,
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

    decorator: Callable[[T], T]

    if service_url:
        decorator = _Integration.from_service_url(service_url, host_response=host_response)
    elif sample and environment:
        decorator = _Integration.from_sample(sample, environment, host_agent=host_agent, host_response=host_response)
    # elif app:
    #     decorator = _Integration.from_app(app, host_response=host_response)
    else:
        raise ValueError("Insufficient parameters to create Integration instance.")
        
    return decorator