"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from microsoft_agents.activity import ConversationReference
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.storage.store_item import StoreItem

if TYPE_CHECKING:
    from microsoft_agents.hosting.core.turn_context import TurnContext
    from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter

# JWT claim keys that are persisted alongside a ConversationReference.
_PERSISTED_CLAIM_KEYS = frozenset({"aud", "azp", "appid", "idtyp", "ver", "iss", "tid"})


class Conversation(StoreItem):
    """
    Bundles a :class:`~microsoft_agents.activity.ConversationReference` together
    with a filtered set of JWT claims so that a proactive continuation can be
    performed without holding onto the full :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`.

    Instances are typically created via
    :meth:`~microsoft_agents.hosting.core.app.proactive.conversation_builder.ConversationBuilder`
    or via :meth:`from_turn_context`.

    :param claims: Filtered JWT claims (``aud``, ``azp``, ``appid``, ``idtyp``,
        ``ver``, ``iss``, ``tid``).  May be a raw ``dict`` or a
        :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`.
    :type claims: dict[str, str] or ClaimsIdentity
    :param conversation_reference: The conversation reference.
    :type conversation_reference: :class:`~microsoft_agents.activity.ConversationReference`
    """

    def __init__(
        self,
        claims: "dict[str, str] | ClaimsIdentity",
        conversation_reference: ConversationReference,
    ) -> None:
        if isinstance(claims, ClaimsIdentity):
            self.claims: dict[str, str] = Conversation.claims_from_identity(claims)
        else:
            self.claims = {
                k: v for k, v in claims.items() if k in _PERSISTED_CLAIM_KEYS
            }
        self.conversation_reference: ConversationReference = conversation_reference

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_turn_context(cls, context: "TurnContext") -> "Conversation":
        """
        Create a :class:`Conversation` from the current turn context.

        :param context: The active turn context.
        :type context: :class:`~microsoft_agents.hosting.core.turn_context.TurnContext`
        :return: A new :class:`Conversation` capturing the current turn's identity
            and conversation reference.
        :rtype: :class:`Conversation`
        """
        from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter

        identity: ClaimsIdentity | None = context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY
        )
        reference = context.activity.get_conversation_reference()
        return cls(identity or {}, reference)

    # ------------------------------------------------------------------
    # Claims helpers
    # ------------------------------------------------------------------

    @staticmethod
    def claims_from_identity(identity: ClaimsIdentity) -> "dict[str, str]":
        """
        Return the subset of claims from *identity* that are relevant for proactive
        messaging (``aud``, ``azp``, ``appid``, ``idtyp``, ``ver``, ``iss``, ``tid``).

        :param identity: The full claims identity.
        :type identity: :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
        :return: Filtered claims dictionary.
        :rtype: dict[str, str]
        """
        return {k: v for k, v in identity.claims.items() if k in _PERSISTED_CLAIM_KEYS}

    @staticmethod
    def identity_from_claims(claims: "dict[str, str]") -> ClaimsIdentity:
        """
        Reconstruct a :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
        from a previously persisted claims dict.

        :param claims: Filtered claims dictionary (as produced by :meth:`claims_from_identity`).
        :type claims: dict[str, str]
        :return: Reconstituted claims identity.
        :rtype: :class:`~microsoft_agents.hosting.core.authorization.ClaimsIdentity`
        """
        return ClaimsIdentity(claims=dict(claims), is_authenticated=True)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Raise :exc:`ValueError` if required fields are missing.

        :raises ValueError: If ``conversation_reference``, its nested
            ``conversation``, or ``service_url`` are absent.
        """
        if not self.conversation_reference:
            raise ValueError("Conversation.conversation_reference is required.")
        if not self.conversation_reference.conversation:
            raise ValueError(
                "Conversation.conversation_reference.conversation is required."
            )
        if not self.conversation_reference.conversation.id:
            raise ValueError(
                "Conversation.conversation_reference.conversation.id is required."
            )
        if not self.conversation_reference.service_url:
            raise ValueError(
                "Conversation.conversation_reference.service_url is required."
            )

    # ------------------------------------------------------------------
    # StoreItem serialization
    # ------------------------------------------------------------------

    def store_item_to_json(self) -> dict:
        return {
            "claims": self.claims,
            "conversation_reference": self.conversation_reference.model_dump(
                mode="json", by_alias=True, exclude_unset=True
            ),
        }

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "Conversation":
        reference = ConversationReference.model_validate(
            json_data.get("conversation_reference", {})
        )
        return Conversation(
            claims=json_data.get("claims", {}),
            conversation_reference=reference,
        )
