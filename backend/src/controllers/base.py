from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


class BaseController(ABC):
    """Abstract base class representing an intersection controller strategy."""

    @abstractmethod
    def update(self, delta_time: float, active_vehicles: List[Vehicle]) -> None:
        """Update the controller state based on elapsed time and active vehicles.

        Args:
            delta_time: Time elapsed since the last tick (seconds).
            active_vehicles: List of all active vehicles in the simulation.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the controller.

        Returns:
            A dictionary containing the controller state matching the shared
            schema.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the controller to its initial state."""
        pass
