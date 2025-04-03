from pydantic import BaseModel


class TenantInfo(BaseModel):
    """Describes a tenant.

    :param id: Unique identifier representing a tenant
    :type id: str
    """

    id: str
