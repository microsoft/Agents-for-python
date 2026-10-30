# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

from logging import Logger
from urllib.parse import urlparse

from microsoft_agents.activity._model_utils import pick_model_dict, SkipNone
from microsoft_agents.activity.config import Configuration, xpath

from .agent_auth_configuration import AgentAuthConfiguration
from .connections.connections_map import _ConnectionMap

_REDACTION_PEEK_LENGTH = 3
_REDACTION_THRESH = _REDACTION_PEEK_LENGTH + 6


def _redact_str(s: str, peek: bool = False) -> str:
    """Redact a string for logging purposes.

    :arg s: The string to redact.
    :type s: str
    :arg peek: Whether to show a peek of the string. Defaults to False.
    :type peek: bool
    :return: The redacted string.
    """
    if peek and len(s) > _REDACTION_THRESH:
        return f"{s[:_REDACTION_PEEK_LENGTH]}..."
    else:
        return "..."


def _redact_str_or_none(s: str | None, peek: bool = False) -> str | None:
    """Redact a string or None for logging purposes.

    :arg s: The string to redact or None.
    :type s: str | None
    :arg peek: Whether to show a peek of the string. Defaults to False.
    :type peek: bool
    :return: The redacted string or None.
    :rtype: str | None
    """
    if s is None:
        return None
    return _redact_str(s, peek=peek)


def _redact_scopes(scopes: list[str] | None) -> str | None:
    """Redact a list of scopes for logging purposes.

    :arg scopes: The list of scopes to redact.
    :type scopes: list[str] | None
    :return: A string summarizing the scopes.
    :rtype: str | None
    """
    if scopes is None:
        return None
    return f"... [{len(scopes)} scope(s)]"


def _redact_url(url: str) -> str:
    """
    Redact a URL for logging purposes.

    :arg url: The URL to redact.
    :type url: str
    :return: The redacted URL.
    :rtype: str
    """
    url = url.strip()
    if not url:
        return ""

    try:
        url_parsed = urlparse(url)
        return f"{url_parsed.scheme}://{url_parsed.netloc}/..."
    except Exception:
        return "..."


def _redact_url_or_none(url: str | None) -> str | None:
    """Redact a URL or None for logging purposes.

    :arg url: The URL to redact or None.
    :type url: str | None
    :return: The redacted URL or None.
    :rtype: str | None
    """
    if url is None:
        return None
    return _redact_url(url)


def _summarize_auth_configs(
    config_map: dict[str, AgentAuthConfiguration | Configuration],
) -> str:
    """
    Summarize the authentication configuration for logging.

    :arg config_map: A dictionary of connection configurations.
    :type config_map: dict[str, :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`]
    :return: A string summarizing the authentication configuration.
    :rtype: str
    """
    summary = []
    for connection_name, config in config_map.items():
        scopes = (
            config.SCOPES
            if isinstance(config, AgentAuthConfiguration)
            else (
                config.get_scopes(xpath("scopes"))
                if config.get(xpath("scopes")) is not None
                else None
            )
        )
        if isinstance(config, AgentAuthConfiguration):
            config = Configuration(vars(config))
        summary.append(
            pick_model_dict(
                CONNECTION=connection_name,
                CONNECTION_NAME=SkipNone(config.get_strn(xpath("connection_name"))),
                CLIENTID=SkipNone(
                    _redact_str_or_none(config.get_strn(xpath("client_id")), peek=True)
                ),
                TENANTID=SkipNone(
                    _redact_str_or_none(config.get_strn(xpath("tenant_id")), peek=True)
                ),
                CLIENTSECRET=SkipNone(
                    _redact_str_or_none(config.get_strn(xpath("client_secret")))
                ),
                AUTHORITY=SkipNone(
                    _redact_url_or_none(
                        config.get_strn(xpath("authority"), xpath("authorityendpoint"))
                    )
                ),
                SCOPES=SkipNone(_redact_scopes(scopes)),
                FEDERATED_CLIENT_ID=SkipNone(
                    _redact_str_or_none(
                        config.get_strn(xpath("federated_client_id")), peek=True
                    )
                ),
                CERT_PFX_FILE=SkipNone(
                    _redact_str_or_none(config.get_strn(xpath("cert_pfx_file")))
                ),
                ALT_BLUEPRINT_ID=SkipNone(
                    _redact_str_or_none(
                        config.get_strn(
                            xpath("alternate_blueprint_connection_name"),
                            xpath("alt_blueprint_id"),
                            xpath("alt_blueprint_name"),
                        ),
                        peek=True,
                    )
                ),
                IDPM_RESOURCE=SkipNone(
                    _redact_url_or_none(config.get_strn(xpath("idpm_resource")))
                ),
                AZURE_REGION=SkipNone(
                    _redact_url_or_none(
                        config.get_strn(
                            xpath("azure_region"), xpath("regional_authority")
                        )
                    )
                ),
                ANONYMOUS_ALLOWED=str(
                    config.get_bool(xpath("anonymous_allowed"), default=False)
                ),
            )
        )
    return json.dumps(summary, indent=2)


def _summarize_connections_map(
    connections_map: list[dict[str, str]] | _ConnectionMap,
) -> str:
    if isinstance(connections_map, _ConnectionMap):
        connections_map = [
            {
                "CONNECTION": item.connection,
                "AUDIENCE": item.audience,
                "SERVICEURL": item.service_url,
            }
            for item in connections_map
        ]
    connections_map_output = []
    for mapping in connections_map:
        obj = {
            "CONNECTION": mapping.get("CONNECTION", ""),
        }

        if "AUDIENCE" in mapping:
            obj["AUDIENCE"] = mapping["AUDIENCE"]

        if "SERVICEURL" in mapping:
            service_url = mapping.get("SERVICEURL", "").strip()
            if service_url != "*":
                service_url = _redact_url(service_url)
            obj["SERVICEURL"] = service_url

        connections_map_output.append(obj)

    return json.dumps(connections_map_output, indent=2)


def _log_config(
    logger: Logger,
    config_map: dict[str, AgentAuthConfiguration | Configuration],
    connections_map: list[dict[str, str]] | _ConnectionMap,
) -> None:
    """
    Log the configuration of the MSAL connection manager.

    :arg logger: The logger to use for logging.
    :type logger: :class:`logging.Logger`
    :arg connections_map: A list of connection mappings.
    :type connections_map: list[dict[str, str]]
    :arg config_map: A dictionary of connection configurations.
    :type config_map: dict[str, :class:`microsoft_agents.hosting.core.AgentAuthConfiguration`]
    """

    connections_output = _summarize_auth_configs(config_map)
    connections_map_output = _summarize_connections_map(connections_map)

    logger.info(
        "\nConnections:\n%s\n\nConnections Map:\n%s",
        connections_output,
        connections_map_output,
    )
