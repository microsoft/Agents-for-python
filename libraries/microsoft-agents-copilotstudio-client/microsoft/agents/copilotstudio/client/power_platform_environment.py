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
        cloud_base_address: Optional[str] = None,
    ) -> str:
        if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
            raise ValueError(
                "cloud_base_address must be provided when PowerPlatformCloud is Other"
            )
        if not settings.environment_id:
            raise ValueError("EnvironmentId must be provided")
        if not settings.agent_identifier:
            raise ValueError("AgentIdentifier must be provided")
        if settings.cloud and settings.cloud != PowerPlatformCloud.UNKNOWN:
            cloud = settings.cloud
        if cloud == PowerPlatformCloud.OTHER:
            parsed_url = urlparse(cloud_base_address)
            is_absolute_url = parsed_url.scheme and parsed_url.netloc
            if cloud_base_address and is_absolute_url:
                pass
            elif settings.custom_power_platform_cloud:
                cloud_base_address = settings.custom_power_platform_cloud
            else:
                raise ValueError(
                    "Either CustomPowerPlatformCloud or cloud_base_address must be provided when PowerPlatformCloud is Other"
                )
        if settings.copilot_agent_type:
            agent_type = settings.copilot_agent_type

        cloud_base_address = cloud_base_address or "api.unknown.powerplatform.com"
        host = PowerPlatformEnvironment.get_environment_endpoint(
            cloud, settings.environment_id, cloud_base_address
        )
        return PowerPlatformEnvironment.create_uri(
            settings.agent_identifier, host, agent_type, conversation_id
        )

    @staticmethod
    def get_token_audience(
        settings: Optional[ConnectionSettings] = None,
        cloud: PowerPlatformCloud = PowerPlatformCloud.UNKNOWN,
        cloud_base_address: Optional[str] = None,
    ) -> str:
        if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
            raise ValueError(
                "cloud_base_address must be provided when PowerPlatformCloud is Other"
            )
        if not settings and cloud == PowerPlatformCloud.UNKNOWN:
            raise ValueError("Either settings or cloud must be provided")
        if settings and settings.cloud and settings.cloud != PowerPlatformCloud.UNKNOWN:
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
                    "Either CustomPowerPlatformCloud or cloud_base_address must be provided when PowerPlatformCloud is Other"
                )

        cloud_base_address = cloud_base_address or "api.unknown.powerplatform.com"
        return f"https://{PowerPlatformEnvironment.get_endpoint_suffix(cloud, cloud_base_address)}/.default"

    @staticmethod
    def create_uri(
        agent_identifier: str,
        host: str,
        agent_type: AgentType,
        conversation_id: Optional[str],
    ) -> str:
        agent_path_name = (
            "dataverse-backed" if agent_type == AgentType.PUBLISHED else "prebuilt"
        )
        path = f"/copilotstudio/{agent_path_name}/authenticated/bots/{agent_identifier}/conversations"
        if conversation_id:
            path += f"/{conversation_id}"
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
    def get_environment_endpoint(
        cloud: PowerPlatformCloud,
        environment_id: str,
        cloud_base_address: Optional[str] = None,
    ) -> str:
        if cloud == PowerPlatformCloud.OTHER and not cloud_base_address:
            raise ValueError(
                "cloud_base_address must be provided when PowerPlatformCloud is Other"
            )
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
