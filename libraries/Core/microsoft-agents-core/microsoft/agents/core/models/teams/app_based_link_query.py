from pydantic import BaseModel


class AppBasedLinkQuery(BaseModel):
    """Invoke request body type for app-based link query.

    :param url: Url queried by user
    :type url: str
    :param state: The magic code for OAuth Flow
    :type state: str
    """

    url: str
    state: str
