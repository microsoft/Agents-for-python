# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging


def _configure_logging(logging_config: dict):
    """Configures logging based on the provided logging configuration dictionary.

    :param logging_config: A dictionary containing logging configuration.
    :raises ValueError: If an invalid log level is provided in the configuration.
    """

    levels_map = logging.getLevelNamesMapping()

    log_levels = logging_config.get("LOGLEVEL", {})

    for key in log_levels.keys():
        level_name = log_levels[key].upper()
        if level_name == "INFORMATION":  # .NET parity
            level_name = "INFO"
        level = levels_map.get(level_name)
        if not level:
            raise ValueError(f"Invalid configured log level: {level_name}")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
            )
        )

        namespace = key.lower()
        if namespace == "default":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(namespace)

        logger.addHandler(console_handler)
        logger.setLevel(level)
