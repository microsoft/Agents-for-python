from pydantic import BaseModel


class MessagingExtensionQueryOptions(BaseModel):
    """Messaging extension query options.

    :param skip: Number of entities to skip
    :type skip: int
    :param count: Number of entities to fetch
    :type count: int
    """

    skip: int
    count: int
