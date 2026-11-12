# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration
from ._logging import _configure_logging
from ._engine._resolve import _resolve
from ._metadata import _RootConfigMetadata


def load_configuration_from_env(config_dict: Mapping[str, Any]) -> Configuration:
    """Normalize one configuration mapping, mark it as root, and apply logging.

    Pass ``os.environ`` or an application-prepared mapping. Callers control
    source selection, merging, and precedence before this call. Typed settings
    conversion happens when values are read or bound.

    :param config_dict: Configuration data supplied to the source resolver.
    :return: A Configuration carrying application-root mapping metadata for
        settings binders. Its diagnostic base path is independent of root status.
    """
    config = Configuration(_resolve(config_dict))
    _RootConfigMetadata.set(config, True)
    _configure_logging(config)
    return config
