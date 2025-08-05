# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# enable viewing logs to terminal with colors
# needs to be imported before sys
import colorama
colorama.init(convert=True)

import sys
import logging

from .agent import AGENT_APP, CONNECTION_MANAGER
from .start_server import start_server

# credit to https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# configure rootlogging to console
logging.basicConfig(
    level=logging.INFO,
    format="\n%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # handlers=[
    #     logging.StreamHandler(sys.stdout)
    # ]
    # adding this handler will log for dependencies as well
)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())

ms_agents_logger = logging.getLogger("microsoft.agents")
# ms_agents_logger.addHandler(ch)
ms_agents_logger.setLevel(logging.INFO)
# ms_agents_logger.propagate = False  # Prevent duplicate logs

# Set specific log levels for different components
# logging.getLogger("microsoft.agents.hosting.core.app.agent_application").setLevel(logging.DEBUG)
# logging.getLogger("microsoft.agents.authentication.msal").setLevel(logging.INFO)
# logging.getLogger("microsoft.agents.hosting.core.connector").setLevel(logging.WARNING)

# Log startup message
root_logger = logging.getLogger("microsoft.agents")
root_logger.info("Starting server with enhanced logging...")

start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
