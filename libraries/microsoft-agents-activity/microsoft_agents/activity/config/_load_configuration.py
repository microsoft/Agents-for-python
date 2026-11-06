# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration

from ._logging import _configure_logging


def load_configuration_from_env(
    env_vars: Mapping[str, Any], defaults: Mapping[str, Any] | None = None
) -> Configuration:
    """Resolve environment values and defaults into root configuration.

    Environment-style ``__`` paths are expanded and indexed mappings become
    lists. Environment values take precedence over defaults without modifying
    either input. The resolved logging section is applied before returning.

    :param env_vars: A mapping of environment variable names to their values.
    :param defaults: Optional fallback values, either nested or environment-style.
    :return: A Configuration with ``is_root_config=True``, suitable for binding
        application-level settings. Extracted sections are scoped configurations.
    """
    config = Configuration.resolve(env_vars, defaults or {}, _is_root_config=True)
    _configure_logging(config)
    return config
