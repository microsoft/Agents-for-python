# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Factory for creating task module responses."""

from microsoft.agents.core.models.teams import (
    TaskModuleResponse,
    TaskModuleTaskInfo,
    TaskModuleResponseBase,
)


class TaskModuleResponseFactory:
    """Factory for creating task module responses."""

    @staticmethod
    def to_task_module_response(task_info: TaskModuleTaskInfo) -> TaskModuleResponse:
        """
        Convert a TaskModuleTaskInfo to a TaskModuleResponse.

        Args:
            task_info: The task info to convert.

        Returns:
            A TaskModuleResponse instance.
        """
        return TaskModuleResponseFactory.create_response(task_info)

    @staticmethod
    def create_response(task_info: TaskModuleTaskInfo) -> TaskModuleResponse:
        """
        Create a TaskModuleResponse with type 'continue' and the provided task info as value.

        Args:
            task_info: The task info to use as value.

        Returns:
            A TaskModuleResponse instance.
        """
        task_module_response_base = TaskModuleResponseBase(
            type="continue", value=task_info
        )

        return TaskModuleResponse(type=task_module_response_base)

    @staticmethod
    def create_message_response(message: str) -> TaskModuleResponse:
        """
        Create a TaskModuleResponse with type 'message' and the provided message as value.

        Args:
            message: The message to use as value.

        Returns:
            A TaskModuleResponse instance.
        """
        task_module_response_base = TaskModuleResponseBase(
            type="message", value=message
        )

        return TaskModuleResponse(type=task_module_response_base)
