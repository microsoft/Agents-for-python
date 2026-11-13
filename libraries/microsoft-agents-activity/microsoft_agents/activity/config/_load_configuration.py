# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration
from ._logging import _configure_logging
from ._engine._resolve import _resolve
from ._metadata import _RootConfigMetadata


def load_configuration_from_env(config_dict: Mapping[str, Any]) -> Configuration:
    """Load application settings from environment variables or a dictionary.

    Pass ``os.environ`` to read the current process environment, or supply your
    own dictionary. Names containing ``__`` or ``::`` become nested sections;
    key capitalization is preserved. Values such as ``"30"`` and ``"false"``
    remain strings until you read them with a typed getter.

    For example, without changing the process environment::

        >>> from microsoft_agents.activity.config import load_configuration_from_env
        >>> config = load_configuration_from_env({
        ...     "SERVICE__TIMEOUT": "30",
        ...     "SERVICE__ENABLED": "false",
        ... })
        >>> config.get_int(["SERVICE", "TIMEOUT"])
        30
        >>> config.get_bool(["SERVICE", "ENABLED"])
        False

    The result represents the full application configuration. APIs such as
    ``Authorization`` can use it to find their own sections automatically.
    If a ``logging`` section is present, its log levels are applied as well.

    This function accepts one dictionary. If settings come from several
    sources, combine them first and decide which source should take precedence.

    :param config_dict: Environment variables or other application settings.
    :return: Configuration ready to pass to SDK application components.
    """
    config = Configuration(_resolve(config_dict))
    _RootConfigMetadata.set(config, True)
    _configure_logging(config)
    return config
