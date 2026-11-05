# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration

from ._logging import _configure_logging


def load_configuration_from_env(
    env_vars: Mapping[str, Any], defaults: Mapping[str, Any] | None = None
) -> Configuration:
    """
    Parses environment variables and returns a Configuration object with the relevant configuration.

    :param env_vars: A mapping of environment variable names to their values.
    :param defaults: A mapping of default configuration values.
    :return: A Configuration object containing the resolved configuration.
    """
    config = Configuration.resolve(env_vars, defaults or {}, _is_root_config=True)
    _configure_logging(config)
    return config
