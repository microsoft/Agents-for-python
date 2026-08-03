# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared helpers for recognizing Microsoft Entra ID / Bot Framework token issuers.

Centralizes the cloud (public vs. US Government) and tenant-GUID parsing rules
used by both :class:`AgentAuthConfiguration` (default ``ISSUERS``) and
:class:`JwtTokenValidator` (issuer allow-list validation, tid-to-issuer
binding, and JWKS routing) so the two stay consistent.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
from urllib.parse import urlparse

# Well-known Microsoft first-party token issuer tenant IDs that are always
# trusted, mirroring the default ``ValidIssuers`` set used by the .NET SDK.
# These identify Microsoft infrastructure tenants used by Azure Bot Service,
# Teams and skill/agent-to-agent flows, so enabling issuer validation does not
# reject legitimate first-party traffic.
WELL_KNOWN_PUBLIC_TENANT_IDS = (
    "d6d49420-f39b-4df7-a1dc-d59a935871db",
    "f8cdef31-a31e-4b4a-93e4-5f571e91255a",
    "69e9b82d-4842-4902-8d1e-abc5b98a55e8",
)
WELL_KNOWN_GOV_TENANT_ID = "cab8a31a-1906-4287-a0d8-4eef66b95f6e"

BOTFRAMEWORK_PUBLIC_ISSUER = "https://api.botframework.com"
BOTFRAMEWORK_GOV_ISSUER = "https://api.botframework.us"

BOTFRAMEWORK_JWKS_URIS = {
    BOTFRAMEWORK_PUBLIC_ISSUER: "https://login.botframework.com/v1/.well-known/keys",
    BOTFRAMEWORK_GOV_ISSUER: "https://login.botframework.azure.us/v1/.well-known/keys",
}

_GOV_AUTHORITY_RE = re.compile(r"login\.microsoftonline\.us", re.IGNORECASE)
_ENTRA_TENANT_GUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
_V1_ISSUER_RE = re.compile(r"^https://sts\.windows\.net/([^/]+)/$", re.IGNORECASE)
_V2_ISSUER_RE = re.compile(
    r"^(?i:https://login\.microsoftonline\.(com|us)/)([^/]+)/v2\.0$"
)


class EntraIssuerInfo(NamedTuple):
    """Cloud-affinity metadata for a recognized Entra issuer."""

    tenant: str
    """The lowercased tenant GUID embedded in the issuer."""

    gov: bool | None
    """``True``/``False`` for a cloud-specific v2 issuer (US Gov / public), or
    ``None`` for the cloud-agnostic v1 ``sts.windows.net`` host, which is
    shared across the public and US Government clouds."""


def is_gov_authority(authority: str | None) -> bool:
    """Returns whether the configured authority targets Azure US Government."""
    return bool(authority) and bool(_GOV_AUTHORITY_RE.search(authority))


def effective_tenant(tenant_id: str | None, authority: str | None) -> str | None:
    """Returns the effective tenant identifier for a connection.

    The tenant segment embedded in ``authority``'s path (e.g.
    ``https://login.microsoftonline.com/common`` or
    ``.../{tenant-guid}``) takes precedence over a separately configured
    ``tenant_id`` when present, mirroring the JS reference's
    ``getEffectiveTenant``/``resolveAuthority`` precedence: the authority is
    the more specific/authoritative signal when both are configured. Falls
    back to ``tenant_id`` when ``authority`` has no path segment (or is not
    configured).
    """
    if authority:
        segments = [
            segment
            for segment in urlparse(authority.rstrip("/")).path.split("/")
            if segment
        ]
        if segments:
            return segments[-1]
    return tenant_id


def entra_issuer_info(iss: Any) -> EntraIssuerInfo | None:
    """Parses a recognized public or US Government Entra issuer.

    Only GUID tenants are recognized: a token's ``tid`` claim is always the
    tenant GUID, so an issuer whose tenant segment is a domain alias (e.g.
    ``contoso.onmicrosoft.com``) cannot be compared to ``tid`` and is
    intentionally left unrecognized. Non-Entra issuers such as the Azure Bot
    Service ``api.botframework.*`` issuers carry no ``tid`` claim and are not
    matched here.

    :return: The issuer's tenant and cloud affinity, or ``None`` when ``iss``
        is not a (non-empty) string, or is not a recognized Entra issuer with
        a GUID tenant. A non-string ``iss`` (e.g. a malformed array/object
        claim) is rejected up front rather than passed to the regexes, which
        require string/buffer-like input.
    """
    if not isinstance(iss, str) or not iss:
        return None

    v1_match = _V1_ISSUER_RE.match(iss)
    if v1_match:
        tenant = v1_match.group(1)
        if _ENTRA_TENANT_GUID_RE.match(tenant):
            return EntraIssuerInfo(tenant.lower(), None)
        return None

    v2_match = _V2_ISSUER_RE.match(iss)
    if v2_match:
        cloud, tenant = v2_match.group(1), v2_match.group(2)
        if _ENTRA_TENANT_GUID_RE.match(tenant):
            return EntraIssuerInfo(tenant.lower(), cloud.lower() == "us")
    return None


def default_connection_issuers(
    tenant_id: str | None, authority: str | None
) -> list[str]:
    """Builds the default (tenant-scoped) issuer allow-list for a connection.

    Used when ``ISSUERS`` were not explicitly configured. The effective
    tenant (authority-embedded segment, when present, otherwise
    ``tenant_id``; see :func:`effective_tenant`) is used so an
    authority-scoped concrete or ``common``/``organizations`` tenant is
    reflected correctly instead of falling back to a stale/absent
    ``tenant_id``.
    """
    tenant = effective_tenant(tenant_id, authority) or "common"
    gov = is_gov_authority(authority)
    bf_issuer = BOTFRAMEWORK_GOV_ISSUER if gov else BOTFRAMEWORK_PUBLIC_ISSUER
    login_host = (
        "https://login.microsoftonline.us"
        if gov
        else "https://login.microsoftonline.com"
    )
    return [
        bf_issuer,
        f"https://sts.windows.net/{tenant}/",
        f"{login_host}/{tenant}/v2.0",
    ]


def well_known_first_party_issuers(authority: str | None) -> list[str]:
    """Returns the well-known Microsoft first-party issuers always trusted for
    the cloud implied by ``authority`` (public by default, US Government when
    the authority is a US Government endpoint)."""
    if is_gov_authority(authority):
        return [
            BOTFRAMEWORK_GOV_ISSUER,
            f"https://sts.windows.net/{WELL_KNOWN_GOV_TENANT_ID}/",
            f"https://login.microsoftonline.us/{WELL_KNOWN_GOV_TENANT_ID}/v2.0",
        ]
    issuers = [BOTFRAMEWORK_PUBLIC_ISSUER]
    for tenant in WELL_KNOWN_PUBLIC_TENANT_IDS:
        issuers.append(f"https://sts.windows.net/{tenant}/")
        issuers.append(f"https://login.microsoftonline.com/{tenant}/v2.0")
    return issuers


def jwks_login_host(authority: str | None) -> str:
    """Returns the Entra discovery-keys login host for the configured cloud."""
    return (
        "https://login.microsoftonline.us"
        if is_gov_authority(authority)
        else "https://login.microsoftonline.com"
    )
