from pydantic import BaseModel
from typing import Optional


class TaskModuleTaskInfo(BaseModel):
    """Information about a task module task.

    :param title: The title of the task module.
    :type title: Optional[str]
    :param height: The height of the task module.
    :type height: Optional[int]
    :param width: The width of the task module.
    :type width: Optional[int]
    :param url: The URL of the task module.
    :type url: Optional[str]
    :param card: The adaptive card for the task module.
    :type card: Optional[object]
    """

    title: Optional[str]
    height: Optional[int]
    width: Optional[int]
    url: Optional[str]
    card: Optional[object]
