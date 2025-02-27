from enum import Enum


class PowerPlatformCloud(str, Enum):
    """
    Enum representing different Power Platform Clouds.
    """

    Unknown = "Unknown"
    Exp = "Exp"
    Dev = "Dev"
    Test = "Test"
    Preprod = "Preprod"
    FirstRelease = "FirstRelease"
    Prod = "Prod"
    Gov = "Gov"
    High = "High"
    DoD = "DoD"
    Mooncake = "Mooncake"
    Ex = "Ex"
    Rx = "Rx"
    Prv = "Prv"
    Local = "Local"
    GovFR = "GovFR"
    Other = "Other"
