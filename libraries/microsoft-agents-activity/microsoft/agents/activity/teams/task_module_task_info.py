# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from ..attachment import Attachment


class TaskModuleTaskInfo(AgentsModel):
    """Information about a task module task.

    :param title: The title of the task module.
    :type title: str
    :param height: The height of the task module.
    :type height: int
    :param width: The width of the task module.
    :type width: int
    :param url: The URL of the task module.
    :type url: str
    :param card: The adaptive card for the task module.
    :type card: object
    """

    title: str = None
    height: object = None
    width: object = None
    url: str = None
    card: Attachment = None
    fallback_url: str = None
    completion_bot_id: str = None
