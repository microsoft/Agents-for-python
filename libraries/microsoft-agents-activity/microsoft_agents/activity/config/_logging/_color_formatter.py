# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

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
