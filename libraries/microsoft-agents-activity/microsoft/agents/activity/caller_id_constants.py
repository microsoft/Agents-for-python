from enum import Enum


class CallerIdConstants(str, Enum):
    public_azure_channel = "urn:botframework:azure"
    us_gov_channel = "urn:botframework:azureusgov"
    agent_to_agent_prefix = "urn:botframework:aadappid:"
