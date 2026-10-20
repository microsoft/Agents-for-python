# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

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

_DEFAULT_NAMESPACE = "default"