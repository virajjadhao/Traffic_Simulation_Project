from typing import Callable, Dict, Type

from src.controllers.base import BaseController


class ControllerRegistry:
    """Centralized registry for intersection control strategies."""

    _registry: Dict[str, Type[BaseController]] = {}

    @classmethod
    def register(
        cls, type_name: str
    ) -> Callable[[Type[BaseController]], Type[BaseController]]:
        """Decorator to register a controller class under a type name."""

        def decorator(wrapped_class: Type[BaseController]) -> Type[BaseController]:
            cls._registry[type_name] = wrapped_class
            return wrapped_class

        return decorator

    @classmethod
    def get_controller_class(cls, type_name: str) -> Type[BaseController]:
        """Retrieve the registered controller class type.

        Args:
            type_name: The string identifier of the controller type.

        Returns:
            The class type of the requested controller.

        Raises:
            ValueError: If the controller type is not registered.
        """
        if type_name not in cls._registry:
            raise ValueError(f"Controller type '{type_name}' is not registered.")
        return cls._registry[type_name]


def register_controller(
    type_name: str,
) -> Callable[[Type[BaseController]], Type[BaseController]]:
    """Decorator wrapper to register a controller class under a type name."""
    return ControllerRegistry.register(type_name)
