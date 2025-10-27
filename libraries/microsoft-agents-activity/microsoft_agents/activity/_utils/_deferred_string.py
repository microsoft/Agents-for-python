# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class _DeferredString:
    """A wrapper around a function to allow for deferred evaluation.

    The result of the function is converted to a string with str().
    If an error occurs during evaluation, an error is logged and a default
    string is returned.
    """

    def __init__(self, func: Callable, *args, **kwargs):
        """Initializes a DeferredString instance.

        :param func: The function to be called to get the string value.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        try:
            return str(self.func(*self.args, **self.kwargs))
        except Exception as e:
            logger.error("Error evaluating deferred string", exc_info=e)
            return "_DeferredString: error evaluating deferred string"
