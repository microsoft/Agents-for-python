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


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that adds color to log messages based on their severity level."""

    BRIGHT_RED = "\033[1;31m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    RESET = "\033[0m"

    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.CRITICAL: f"{BRIGHT_RED}{log_format}{RESET}",
        logging.ERROR: f"{RED}{log_format}{RESET}",
        logging.WARNING: f"{YELLOW}{log_format}{RESET}",
        logging.INFO: f"{GREEN}{log_format}{RESET}",
        logging.DEBUG: f"{BLUE}{log_format}{RESET}",
        logging.NOTSET: f"{RESET}{log_format}{RESET}",
    }

    def format(self, record):
        """Formats the log record with color based on its severity level."""
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.NOTSET])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _configure_logging(logging_config: dict):
    """Configures logging based on the provided logging configuration dictionary.

    :param logging_config: A dictionary containing logging configuration.
    :raises ValueError: If an invalid log level is provided in the configuration.
    """

    log_levels = logging_config.get("LOGLEVEL", {})

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())

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

        logger.propagate = False  # Prevent log messages from being propagated
        logger.handlers.clear()  # Remove existing handlers to prevent duplicates
        logger.addHandler(console_handler)
        logger.setLevel(level)
