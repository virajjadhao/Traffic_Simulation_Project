from typing import TYPE_CHECKING, List

from src.core.enums import Direction
from src.roads.lane import Lane

if TYPE_CHECKING:
    from src.vehicles.vehicle import Vehicle


class Approach:
    """Represents an approach arm (North, South, East, West) of the intersection."""

    def __init__(self, direction: Direction, speed_limit: float = 13.89) -> None:
        """Initialize the Approach.

        Args:
            direction: The direction enum of the approach.
            speed_limit: Default speed limit for lanes on this approach.

        Raises:
            ValueError: If speed_limit <= 0.
        """
        if speed_limit <= 0:
            raise ValueError("Speed limit must be greater than zero.")
        self._direction: Direction = direction
        self._speed_limit: float = speed_limit
        self._lanes: List[Lane] = []

    @property
    def direction(self) -> Direction:
        """Get the direction of the approach."""
        return self._direction

    @property
    def speed_limit(self) -> float:
        """Get the default speed limit of the approach."""
        return self._speed_limit

    def add_lane(self, lane: Lane) -> None:
        """Add a lane to the approach.

        Args:
            lane: The Lane instance to add.
        """
        if lane not in self._lanes:
            self._lanes.append(lane)

    def get_lanes(self) -> List[Lane]:
        """Get all lanes on this approach.

        Returns:
            List of Lane instances.
        """
        return list(self._lanes)

    def get_active_vehicles(self) -> List["Vehicle"]:
        """Get all active vehicles across all lanes on this approach.

        Returns:
            List of active Vehicle instances.
        """
        vehicles: List["Vehicle"] = []
        for lane in self._lanes:
            vehicles.extend(lane.get_vehicles())
        return vehicles
