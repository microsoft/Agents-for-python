# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration
from ._logging import _configure_logging
from ._engine._resolve import _resolve
from ._engine._utils import _parse_env_var_name
from ._metadata import _RootConfigMetadata

# Top-level SDK keys retained by load_configuration_from_env. Matching
# ignores case but keeps underscores significant.
_SDK_SECTIONS = frozenset(
    name.casefold()
    for name in (
        "Connections",
        "ConnectionsMap",
        "TokenValidation",
        "AgentApplication",
        "OutboundHostValidator",
        "Logging",
        "Port",
    )
)


def _is_sdk_section(key: Any) -> bool:
    section = _parse_env_var_name(str(key)).split("::", 1)[0]
    return section.casefold() in _SDK_SECTIONS


def load_configuration_from_env(config_dict: Mapping[str, Any], /) -> Configuration:
    """Load application settings from environment variables or a dictionary.

    Pass ``os.environ`` to read the current process environment, or supply your
    own dictionary. Names containing ``__`` or ``::`` become nested sections;
    key capitalization is preserved. Values such as ``"30"`` and ``"false"``
    remain strings until you read them with a typed getter.

    Only the SDK's top-level keys are kept: ``Connections``,
    ``ConnectionsMap``, ``TokenValidation``, ``AgentApplication``,
    ``OutboundHostValidator``, ``Logging``, and ``Port``. Names ignore case but
    not underscores, so ``CONNECTIONSMAP`` is kept while ``CONNECTIONS_MAP`` is
    not. Other keys, such as ``PATH`` or unrelated secrets, are discarded.

    For example, without changing the process environment::

        >>> from microsoft_agents.activity.config import load_configuration_from_env
        >>> config = load_configuration_from_env({
        ...     "AGENTAPPLICATION__STARTTYPINGTIMER": "false",
        ...     "CONNECTIONSMAP__0__SERVICEURL": "*",
        ...     "PATH": "/usr/bin",
        ... })
        >>> config.get_bool(["AGENTAPPLICATION", "STARTTYPINGTIMER"])
        False
        >>> config.get(["CONNECTIONSMAP", 0, "SERVICEURL"])
        '*'
        >>> config.get("PATH") is None
        True

    The result represents the full application configuration. APIs such as
    ``Authorization`` can use it to find their own sections automatically.
    If a ``logging`` section is present, its log levels are applied as well.

    This function accepts one dictionary. If settings come from several
    sources, combine them first and decide which source should take precedence.

    :param config_dict: Environment variables or other application settings.
    :return: Configuration ready to pass to SDK application components.
    """
    sdk_settings = {
        key: value for key, value in config_dict.items() if _is_sdk_section(key)
    }
    config = Configuration(_resolve(sdk_settings))
    _RootConfigMetadata.set(config, True)
    _configure_logging(config)
    return config
