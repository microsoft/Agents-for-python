from . import constants


def _format_scopes(scopes: list[str] | None) -> str:
    if not scopes:
        return constants.UNKNOWN
    return ",".join(scopes)
