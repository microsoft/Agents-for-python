from pydantic import BaseModel


class O365ConnectorCardOpenUriTarget(BaseModel):
    """O365 connector card OpenUri target.

    :param os: Target operating system. Possible values include: 'default', 'iOS', 'android', 'windows'
    :type os: str
    :param uri: Target URI.
    :type uri: str
    """

    os: str
    uri: str
