# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.copilotstudio.client.errors import copilot_studio_errors
from urllib.parse import urlparse, urlunparse
from typing import Optional
from .connection_settings import ConnectionSettings
from .agent_type import AgentType
from .power_platform_cloud import PowerPlatformCloud


# TODO: POC provides the
class PowerPlatformEnvironment:
    """
    Class representing the Power Platform Environment.
    """

    API_VERSION = "2022-03-01-preview"

    @staticmethod
    def get_copilot_studio_connection_url(
        settings: ConnectionSettings,
        conversation_id: Optional[str] = None,
        agent_type: AgentType = AgentType.PUBLISHED,
        cloud: PowerPlatformCloud = PowerPlatformCloud.PROD,
        create_subscribe_link: bool = False,
        cloud_base_address: Optional[str] = None,
        direct_connect_url: Optional[str] = None,
    ) -> str:
        """
        Gets the Power Platform API connection URL for the given settings.

        :param settings: Configuration Settings to use
        :param conversation_id: Optional, Conversation ID to address
        :param agent_type: Type of Agent being addressed
        :param cloud: Power Platform Cloud Hosting Agent
        :param create_subscribe_link: Whether to create a subscribe link for the conversation
        :param cloud_base_address: Power Platform API endpoint to use if Cloud is configured as "other"
        :param direct_connect_url: DirectConnection URL to a given Copilot Studio agent, if provided all other settings are ignored
        :return: Connection URL string
        """
        # Check if using DirectConnect URL mode
        direct_url = direct_connect_url or settings.direct_connect_url

        if not direct_url:
            # Standard environment-based connection
            if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
                raise ValueError(str(copilot_studio_errors.CloudBaseAddressRequired))
            if not settings.environment_id:
                raise ValueError(str(copilot_studio_errors.EnvironmentIdRequired))
            if not settings.agent_identifier:
                raise ValueError(str(copilot_studio_errors.AgentIdentifierRequired))
            if settings.cloud and settings.cloud != PowerPlatformCloud.UNKNOWN:
                cloud = settings.cloud
            if cloud == PowerPlatformCloud.OTHER:
                parsed_url = (
                    urlparse(cloud_base_address) if cloud_base_address else None
                )
                is_absolute_url = parsed_url and parsed_url.scheme and parsed_url.netloc
                if cloud_base_address and is_absolute_url:
                    cloud = PowerPlatformCloud.OTHER
                elif settings.custom_power_platform_cloud:
                    parsed_custom = urlparse(settings.custom_power_platform_cloud)
                    if parsed_custom.scheme or parsed_custom.netloc:
                        cloud = PowerPlatformCloud.OTHER
                        cloud_base_address = settings.custom_power_platform_cloud
                    else:
                        raise ValueError(
                            str(copilot_studio_errors.CustomCloudOrBaseAddressRequired)
                        )
                else:
                    raise ValueError(
                        str(copilot_studio_errors.CustomCloudOrBaseAddressRequired)
                    )
            if settings.copilot_agent_type:
                agent_type = settings.copilot_agent_type

            cloud_base_address = cloud_base_address or "api.unknown.powerplatform.com"
            host = PowerPlatformEnvironment.get_environment_endpoint(
                cloud, settings.environment_id, cloud_base_address
            )
            return PowerPlatformEnvironment._create_uri_standard(
                settings.agent_identifier,
                host,
                agent_type,
                conversation_id,
                create_subscribe_link,
            )
        else:
            # DirectConnect URL mode
            parsed_direct = urlparse(direct_url)
            if not (parsed_direct.scheme and parsed_direct.netloc):
                raise ValueError("DirectConnectUrl is invalid")
            return PowerPlatformEnvironment._create_uri_direct(
                direct_url, conversation_id, create_subscribe_link
            )

    @staticmethod
    def get_token_audience(
        settings: Optional[ConnectionSettings] = None,
        cloud: PowerPlatformCloud = PowerPlatformCloud.UNKNOWN,
        cloud_base_address: Optional[str] = None,
        direct_connect_url: Optional[str] = None,
    ) -> str:
        """
        Returns the Power Platform API Audience.

        :param settings: Configuration Settings to use
        :param cloud: Power Platform Cloud Hosting Agent
        :param cloud_base_address: Power Platform API endpoint to use if Cloud is configured as "other"
        :param direct_connect_url: DirectConnection URL to a given Copilot Studio agent
        :return: Token audience string
        """
        # Check if using DirectConnect URL mode
        direct_url = direct_connect_url or (
            settings.direct_connect_url if settings else None
        )

        if not direct_url:
            # Standard environment-based audience
            if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
                raise ValueError(str(copilot_studio_errors.CloudBaseAddressRequired))
            if not settings and cloud == PowerPlatformCloud.UNKNOWN:
                raise ValueError("Either settings or cloud must be provided")
            if (
                settings
                and settings.cloud
                and settings.cloud != PowerPlatformCloud.UNKNOWN
            ):
                cloud = settings.cloud
            if cloud == PowerPlatformCloud.OTHER:
                if cloud_base_address and urlparse(cloud_base_address).scheme:
                    cloud = PowerPlatformCloud.OTHER
                elif (
                    settings
                    and settings.custom_power_platform_cloud
                    and urlparse(settings.custom_power_platform_cloud).scheme
                ):
                    cloud = PowerPlatformCloud.OTHER
                    cloud_base_address = settings.custom_power_platform_cloud
                else:
                    raise ValueError(
                        str(copilot_studio_errors.CustomCloudOrBaseAddressRequired)
                    )

            # Normalize custom cloud base address to host-only (strip any scheme)
            if cloud == PowerPlatformCloud.OTHER and cloud_base_address:
                parsed_base = urlparse(cloud_base_address)
                if parsed_base.scheme and parsed_base.netloc:
                    cloud_base_address = parsed_base.netloc
            cloud_base_address = cloud_base_address or "api.unknown.powerplatform.com"
            return f"https://{PowerPlatformEnvironment.get_endpoint_suffix(cloud, cloud_base_address)}/.default"
        else:
            # DirectConnect URL mode
            parsed_direct = urlparse(direct_url)
            if not (parsed_direct.scheme and parsed_direct.netloc):
                raise ValueError(
                    "Invalid DirectConnectUrl: an absolute URL with scheme and host is required"
                )

            decoded_cloud = PowerPlatformEnvironment._decode_cloud_from_uri(direct_url)
            if decoded_cloud == PowerPlatformCloud.UNKNOWN:
                cloud_to_test = settings.cloud if settings else cloud
                if (
                    cloud_to_test == PowerPlatformCloud.OTHER
                    or cloud_to_test == PowerPlatformCloud.UNKNOWN
                ):
                    raise ValueError(
                        "Unable to resolve the PowerPlatform Cloud from DirectConnectUrl. "
                        "The Token Audience resolver requires a specific PowerPlatformCloudCategory."
                    )
                if cloud_to_test != PowerPlatformCloud.UNKNOWN:
                    return f"https://{PowerPlatformEnvironment.get_endpoint_suffix(cloud_to_test, '')}/.default"
                else:
                    raise ValueError(
                        "Unable to resolve the PowerPlatform Cloud from DirectConnectUrl. "
                        "The Token Audience resolver requires a specific PowerPlatformCloudCategory."
                    )
            return f"https://{PowerPlatformEnvironment.get_endpoint_suffix(decoded_cloud, '')}/.default"

    @staticmethod
    def create_uri(
        agent_identifier: str,
        host: str,
        agent_type: AgentType,
        conversation_id: Optional[str],
        create_subscribe_link: bool = False,
    ) -> str:
        """
        Creates the PowerPlatform API connection URL for the given settings.
        This is a compatibility method that calls _create_uri_standard.

        :param agent_identifier: The agent/bot identifier
        :param host: The host address
        :param agent_type: Type of agent (Published or Prebuilt)
        :param conversation_id: Optional conversation ID
        :param create_subscribe_link: Whether to create a subscribe link
        :return: Connection URL string
        """
        return PowerPlatformEnvironment._create_uri_standard(
            agent_identifier, host, agent_type, conversation_id, create_subscribe_link
        )

    @staticmethod
    def _create_uri_standard(
        agent_identifier: str,
        host: str,
        agent_type: AgentType,
        conversation_id: Optional[str],
        create_subscribe_link: bool = False,
    ) -> str:
        """
        Creates the PowerPlatform API connection URL for standard environment-based connections.

        :param agent_identifier: The agent/bot identifier (schema name)
        :param host: The host address
        :param agent_type: Type of agent (Published or Prebuilt)
        :param conversation_id: Optional conversation ID
        :param create_subscribe_link: Whether to create a subscribe link
        :return: Connection URL string
        """
        agent_path_name = (
            "dataverse-backed" if agent_type == AgentType.PUBLISHED else "prebuilt"
        )

        if not conversation_id:
            path = f"/copilotstudio/{agent_path_name}/authenticated/bots/{agent_identifier}/conversations"
        else:
            conversation_suffix = "/subscribe" if create_subscribe_link else ""
            path = f"/copilotstudio/{agent_path_name}/authenticated/bots/{agent_identifier}/conversations/{conversation_id}{conversation_suffix}"

        return urlunparse(
            (
                "https",
                host,
                path,
                "",
                f"api-version={PowerPlatformEnvironment.API_VERSION}",
                "",
            )
        )

    @staticmethod
    def _create_uri_direct(
        base_address: str,
        conversation_id: Optional[str],
        create_subscribe_link: bool = False,
    ) -> str:
        """
        Creates the PowerPlatform API connection URL using a DirectConnect URL.
        Used only when DirectConnectUrl is provided.

        :param base_address: The direct connect base URL
        :param conversation_id: Optional conversation ID
        :param create_subscribe_link: Whether to create a subscribe link
        :return: Connection URL string
        """
        parsed = urlparse(base_address)

        # Remove trailing slashes
        path = parsed.path
        while path.endswith("/") or path.endswith("\\"):
            path = path[:-1]

        # If path has /conversations, remove it
        if "/conversations" in path:
            path = path[: path.index("/conversations")]

        # Build the new path
        if not conversation_id:
            path = f"{path}/conversations"
        else:
            if create_subscribe_link:
                path = f"{path}/conversations/{conversation_id}/subscribe"
            else:
                path = f"{path}/conversations/{conversation_id}"

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                path,
                "",
                f"api-version={PowerPlatformEnvironment.API_VERSION}",
                "",
            )
        )

    @staticmethod
    def _decode_cloud_from_uri(uri: str) -> PowerPlatformCloud:
        """
        Decode the PowerPlatformCloud from a DirectConnect URL.

        :param uri: The URL to decode
        :return: The PowerPlatformCloud enum value
        """
        parsed = urlparse(uri)
        host = parsed.hostname.lower() if parsed.hostname else ""

        cloud_mapping = {
            "api.powerplatform.localhost": PowerPlatformCloud.LOCAL,
            "api.exp.powerplatform.com": PowerPlatformCloud.EXP,
            "api.dev.powerplatform.com": PowerPlatformCloud.DEV,
            "api.prv.powerplatform.com": PowerPlatformCloud.PRV,
            "api.test.powerplatform.com": PowerPlatformCloud.TEST,
            "api.preprod.powerplatform.com": PowerPlatformCloud.PREPROD,
            "api.powerplatform.com": PowerPlatformCloud.PROD,
            "api.gov.powerplatform.microsoft.us": PowerPlatformCloud.GOV_FR,
            "api.high.powerplatform.microsoft.us": PowerPlatformCloud.HIGH,
            "api.appsplatform.us": PowerPlatformCloud.DOD,
            "api.powerplatform.partner.microsoftonline.cn": PowerPlatformCloud.MOONCAKE,
        }

        return cloud_mapping.get(host, PowerPlatformCloud.UNKNOWN)

    @staticmethod
    def get_environment_endpoint(
        cloud: PowerPlatformCloud,
        environment_id: str,
        cloud_base_address: Optional[str] = None,
    ) -> str:
        if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
            raise ValueError(str(copilot_studio_errors.CloudBaseAddressRequired))
        cloud_base_address = cloud_base_address or "api.unknown.powerplatform.com"
        normalized_resource_id = environment_id.lower().replace("-", "")
        id_suffix_length = PowerPlatformEnvironment.get_id_suffix_length(cloud)
        hex_prefix = normalized_resource_id[:-id_suffix_length]
        hex_suffix = normalized_resource_id[-id_suffix_length:]
        return f"{hex_prefix}.{hex_suffix}.environment.{PowerPlatformEnvironment.get_endpoint_suffix(cloud, cloud_base_address)}"

    @staticmethod
    def get_endpoint_suffix(cloud: PowerPlatformCloud, cloud_base_address: str) -> str:
        return {
            PowerPlatformCloud.LOCAL: "api.powerplatform.localhost",
            PowerPlatformCloud.EXP: "api.exp.powerplatform.com",
            PowerPlatformCloud.DEV: "api.dev.powerplatform.com",
            PowerPlatformCloud.PRV: "api.prv.powerplatform.com",
            PowerPlatformCloud.TEST: "api.test.powerplatform.com",
            PowerPlatformCloud.PREPROD: "api.preprod.powerplatform.com",
            PowerPlatformCloud.FIRST_RELEASE: "api.powerplatform.com",
            PowerPlatformCloud.PROD: "api.powerplatform.com",
            PowerPlatformCloud.GOV_FR: "api.gov.powerplatform.microsoft.us",
            PowerPlatformCloud.GOV: "api.gov.powerplatform.microsoft.us",
            PowerPlatformCloud.HIGH: "api.high.powerplatform.microsoft.us",
            PowerPlatformCloud.DOD: "api.appsplatform.us",
            PowerPlatformCloud.MOONCAKE: "api.powerplatform.partner.microsoftonline.cn",
            PowerPlatformCloud.EX: "api.powerplatform.eaglex.ic.gov",
            PowerPlatformCloud.RX: "api.powerplatform.microsoft.scloud",
            PowerPlatformCloud.OTHER: cloud_base_address,
        }.get(cloud, ValueError(f"Invalid cloud category value: {cloud}"))

    @staticmethod
    def get_id_suffix_length(cloud: PowerPlatformCloud) -> int:
        return (
            2
            if cloud in {PowerPlatformCloud.FIRST_RELEASE, PowerPlatformCloud.PROD}
            else 1
        )
