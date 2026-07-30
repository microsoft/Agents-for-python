# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import ConnectionManager, AnonymousTokenProvider

class AnonymousConnectionManager(ConnectionManager):
    """A ConnectionManager that provides anonymous tokens for testing purposes."""

    def __init__(self):
        super().__init__(lambda c: AnonymousTokenProvider())