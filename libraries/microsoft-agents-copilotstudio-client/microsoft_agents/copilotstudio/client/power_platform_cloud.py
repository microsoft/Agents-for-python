from enum import Enum


class PowerPlatformCloud(str, Enum):
    """
    Enum representing different Power Platform Clouds.
    """

    UNKNOWN = "Unknown"
    EXP = "Exp"
    DEV = "Dev"
    TEST = "Test"
    PREPROD = "Preprod"
    FIRST_RELEASE = "FirstRelease"
    PROD = "Prod"
    GOV = "Gov"
    HIGH = "High"
    DOD = "DoD"
    MOONCAKE = "Mooncake"
    EX = "Ex"
    RX = "Rx"
    PRV = "Prv"
    LOCAL = "Local"
    GOV_FR = "GovFR"
    OTHER = "Other"
