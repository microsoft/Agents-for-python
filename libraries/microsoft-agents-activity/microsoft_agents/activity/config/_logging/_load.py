# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from typing import Mapping

from ..configuration import Configuration
from ._logging_configuration import _LoggingConfiguration
from ._color_formatter import ColorFormatter
from ._constants import _DEFAULT_NAMESPACE


def _configure_logging(_config: Mapping | Configuration | _LoggingConfiguration):
    """Configures logging based on the provided logging configuration dictionary.

    :param config: A Configuration object or _LoggingConfiguration instance containing logging configuration.
    :raises ValueError: If an invalid log level is provided in the configuration.
    """

    if isinstance(_config, Mapping):
        config = _LoggingConfiguration.from_mapping(_config)
    else:
        config = _LoggingConfiguration.from_configuration(_config)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        ColorFormatter(use_colors=console_handler.stream.isatty())
    )

    for entry in config.log_levels:
        if entry.namespace == _DEFAULT_NAMESPACE:
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(entry.namespace)
        logger.propagate = False  # Prevent log messages from being propagated
        logger.handlers.clear()  # Remove existing handlers to prevent duplicates
        logger.addHandler(console_handler)
        logger.setLevel(entry.level)
