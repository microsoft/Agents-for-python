# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List


class ComponentRegistration:
    """
    Simple component registration that allows dialogs and other components
    to register memory scopes and path resolvers.
    """

    _components: List = []

    @classmethod
    def add(cls, component: object) -> None:
        """
        Register a component. Duplicate types are ignored.
        :param component: The component instance to register.
        """
        if not any(type(c) == type(component) for c in cls._components):
            cls._components.append(component)

    @classmethod
    def get_components(cls) -> List:
        """
        Gets all registered components.
        :return: List of registered component instances.
        """
        return list(cls._components)
