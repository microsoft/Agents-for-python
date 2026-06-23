# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import contextvars
import logging
from typing import Optional

from .header_value_provider import HeaderValueProvider

logger = logging.getLogger(__name__)


class HeaderPropagationContext:
    """Per-turn registry of :class:`HeaderValueProvider` instances whose headers
    are applied to outgoing connector clients.

    The registry is backed by a :class:`contextvars.ContextVar`, so providers
    registered while a turn is being processed are visible to connector clients
    created within that same asynchronous flow without leaking across concurrent
    turns running in separate tasks.
    """

    _providers: contextvars.ContextVar[Optional[list[HeaderValueProvider]]] = (
        contextvars.ContextVar("header_propagation_providers", default=None)
    )

    @classmethod
    def reset(cls) -> None:
        """Starts a fresh, empty provider list for the current turn.

        Call this at the start of a turn before registering providers to avoid
        carrying providers over from a previous turn that shared the same
        context.
        """
        cls._providers.set([])

    @classmethod
    def register(cls, provider: HeaderValueProvider) -> None:
        """Registers a provider for the current turn.

        :param provider: The provider to register.
        :type provider: :class:`HeaderValueProvider`
        """
        providers = cls._providers.get()
        if providers is None:
            providers = []
            cls._providers.set(providers)
        providers.append(provider)

    @classmethod
    def providers(cls) -> list[HeaderValueProvider]:
        """Returns the providers registered for the current turn.

        :return: A copy of the registered providers.
        :rtype: list[:class:`HeaderValueProvider`]
        """
        return list(cls._providers.get() or [])

    @classmethod
    def collect_headers(cls) -> dict[str, str]:
        """Collects and merges the headers produced by all registered providers.

        :return: The merged headers to apply to outgoing requests.
        :rtype: dict[str, str]
        """
        headers: dict[str, str] = {}
        for provider in cls._providers.get() or []:
            try:
                headers.update(provider.get_headers())
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "Header provider %s failed to produce headers",
                    type(provider).__name__,
                )
        return headers
