# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from ..errors import configuration_errors

# in Python 3.11, we can move to using
# logging.getLevelNamesMapping()
_NAME_TO_LEVEL = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "INFORMATION": logging.INFO,  # .NET parity
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _configure_logging(logging_config: dict):
    """Configures logging based on the provided logging configuration dictionary.

    :param logging_config: A dictionary containing logging configuration.
    :raises ValueError: If an invalid log level is provided in the configuration.
    """

    log_levels = logging_config.get("LOGLEVEL", {})

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        )
    )

    for key in log_levels:
        level_name = log_levels[key].upper()
        level = _NAME_TO_LEVEL.get(level_name)
        if level is None:
            raise ValueError(
                configuration_errors.InvalidLoggingConfiguration.format(key, level_name)
            )

        namespace = key.lower()
        if namespace == "default":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(namespace)

        logger.handlers.clear()  # Remove existing handlers to prevent duplicates
        logger.addHandler(console_handler)
        logger.setLevel(level)
