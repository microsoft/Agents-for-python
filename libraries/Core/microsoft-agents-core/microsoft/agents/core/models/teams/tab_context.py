from pydantic import BaseModel


class TabContext(BaseModel):
    """Current tab request context, i.e., the current theme.

    :param theme: Gets or sets the current user's theme.
    :type theme: str
    """

    theme: str
