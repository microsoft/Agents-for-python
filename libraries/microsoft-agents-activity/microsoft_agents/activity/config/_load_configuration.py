# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration

from ._logging import _configure_logging
from ._utils import _xpath, _resolve


def load_configuration_from_env(
    env_vars: Mapping[str, Any], defaults: Mapping[str, Any] | None = None
) -> Configuration:
    """
    Parses environment variables and returns a Configuration object with the relevant configuration.

    :param env_vars: A mapping of environment variable names to their values.
    :param defaults: A mapping of default configuration values.
    :return: A Configuration object containing the resolved configuration.
    """
    local_vars = dict(env_vars)

    resolved = _resolve(local_vars, defaults or {})
    config = Configuration(resolved)
    _configure_logging(config.get_section(_xpath("logging"), default=None) or Configuration())

    config["AgentApplication"] = config.pop("AgentApplication", {})
    config["Connections"] = config.pop("Connections", {})
    config["ConnectionsMap"] = config.pop("ConnectionsMap", [])

    return config