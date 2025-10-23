# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

logger = logging.getLogger(__name__)


class _DeferredString:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        try:
            return str(self.func(*self.args, **self.kwargs))
        except Exception as e:
            logger.error("Error evaluating deferred string", exc_info=e)
            return "_DeferredString: error evaluating deferred string"
