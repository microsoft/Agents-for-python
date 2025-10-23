# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
    
class _DeferredString:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return str(self.func(*self.args, **self.kwargs))