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
    """Logging formatter that can add ANSI color based on severity."""

    MAGENTA = "\033[1;35m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[1;32m"
    BLUE = "\033[1;34m"
    RESET = "\033[0m"

    FMT = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    def __init__(
        self,
        use_colors: bool = True,
    ) -> None:
        super().__init__(fmt=self.FMT)
        self._plain_formatter = logging.Formatter(fmt=self.FMT)
        if not use_colors:
            self._formatters: dict[int, logging.Formatter] = {}
            return
        self._formatters = {
            logging.CRITICAL: logging.Formatter(
                f"{self.MAGENTA}{self.FMT}{self.RESET}"
            ),
            logging.ERROR: logging.Formatter(f"{self.RED}{self.FMT}{self.RESET}"),
            logging.WARNING: logging.Formatter(f"{self.YELLOW}{self.FMT}{self.RESET}"),
            logging.INFO: logging.Formatter(f"{self.GREEN}{self.FMT}{self.RESET}"),
            logging.DEBUG: logging.Formatter(f"{self.BLUE}{self.FMT}{self.RESET}"),
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self._formatters.get(record.levelno)
        return (formatter or self._plain_formatter).format(record)


def _configure_logging(logging_config: dict):
    """Configures logging based on the provided logging configuration dictionary.

    :param logging_config: A dictionary containing logging configuration.
    :raises ValueError: If an invalid log level is provided in the configuration.
    """

    log_levels = logging_config.get("LOGLEVEL", {})

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        ColorFormatter(use_colors=console_handler.stream.isatty())
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

        logger.propagate = False  # Prevent log messages from being propagated
        logger.handlers.clear()  # Remove existing handlers to prevent duplicates
        logger.addHandler(console_handler)
        logger.setLevel(level)
