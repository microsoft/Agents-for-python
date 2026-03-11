# from enum import Enum

# from abc import ABC, abstractmethod
# from collections.abc import AsyncIterator
# from contextlib import asynccontextmanager

# from dotenv import dotenv_values

# from microsoft_agents.activity import load_configuration_from_env

# from .core import (
#     _AiohttpClientFactory,
#     AiohttpCallbackServer,
#     ClientFactory,
#     Scenario,
#     ScenarioConfig,
# )

# class SDKType(Enum, str):
#     PYTHON = "python"
#     JS = "js"
#     NET = "net"

# class ScriptScenario(Scenario, ABC):

#     def __init__(self, sdk_type: SDKType, config: ScenarioConfig | None = None) -> None:
#         super().__init__(config)
#         self._sdk_type = sdk_type

#     async def _run_script(self):
#         raise NotImplementedError("Subclasses must implement _run_code to execute the test scenario.")

#     @asynccontextmanager
#     async def run(self) -> AsyncIterator[ClientFactory]:
#         """Start callback server and yield a client factory."""

#         res = await self._run_script()
        
#         env_vars = dotenv_values(self._config.env_file_path)
#         sdk_config = load_configuration_from_env(env_vars)
        
#         callback_server = AiohttpCallbackServer(self._config.callback_server_port)

#         async with callback_server.listen() as transcript:
#             # Create a factory that binds the agent URL, callback endpoint,
#             # and SDK config so callers can create configured clients
#             factory = _AiohttpClientFactory(
#                 agent_url=self._endpoint,
#                 response_endpoint=callback_server.service_endpoint,
#                 sdk_config=sdk_config,
#                 default_config=self._config.client_config,
#                 transcript=transcript,
#             )
            
#             try:
#                 yield factory
#             finally:
#                 await factory.cleanup()