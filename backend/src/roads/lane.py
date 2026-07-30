import math
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from src.vehicles.vehicle import Vehicle


class Lane:
    """Represents a single lane corridor on an approach road."""

    def __init__(
        self,
        lane_id: str,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        speed_limit: float = 13.89,
    ) -> None:
        """Initialize the Lane.

        Args:
            lane_id: Unique identifier for the lane.
            start_x: X-coordinate of the lane start (meters).
            start_y: Y-coordinate of the lane start (meters).
            end_x: X-coordinate of the lane end (meters).
            end_y: Y-coordinate of the lane end (meters).
            speed_limit: Max allowed speed limit (meters/second).

        Raises:
            ValueError: If coordinates are identical (zero length) or speed_limit <= 0.
        """
        if start_x == end_x and start_y == end_y:
            raise ValueError(
                "Lane start and end points cannot be identical "
                "(length must be non-zero)."
            )
        if speed_limit <= 0:
            raise ValueError("Speed limit must be greater than zero.")

        self._lane_id: str = lane_id
        self._start_x: float = start_x
        self._start_y: float = start_y
        self._end_x: float = end_x
        self._end_y: float = end_y
        self._speed_limit: float = speed_limit
        self._active_vehicles: List["Vehicle"] = []

    @property
    def lane_id(self) -> str:
        """Get the lane ID."""
        return self._lane_id

    @property
    def start_coords(self) -> Tuple[float, float]:
        """Get the start coordinates of the lane (start_x, start_y)."""
        return self._start_x, self._start_y

    @property
    def end_coords(self) -> Tuple[float, float]:
        """Get the end coordinates of the lane (end_x, end_y)."""
        return self._end_x, self._end_y

    @property
    def speed_limit(self) -> float:
        """Get the speed limit of the lane."""
        return self._speed_limit

    @property
    def length(self) -> float:
        """Get the physical length of the lane in meters."""
        return math.hypot(self._end_x - self._start_x, self._end_y - self._start_y)

    @property
    def vector(self) -> Tuple[float, float]:
        """Get the directional vector of the lane (dx, dy)."""
        return self._end_x - self._start_x, self._end_y - self._start_y

    @property
    def heading(self) -> float:
        """Get the compass heading of the lane in degrees clockwise from North.

        Calculated relative to positive Y.

        Returns:
            Heading in degrees in the range [0.0, 360.0).
        """
        dx, dy = self.vector
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad) % 360.0

    def get_point_at_distance(self, distance: float) -> Tuple[float, float]:
        """Compute coordinates (x, y) at a given distance along the lane center line.

        If distance exceeds the lane length, it is capped at the lane end point.
        If distance is negative, it is capped at the lane start point.

        Args:
            distance: Distance in meters from the start of the lane.

        Returns:
            A tuple of (x, y) coordinates.
        """
        length = self.length
        if distance <= 0:
            return self.start_coords
        if distance >= length:
            return self.end_coords

        t = distance / length
        x = self._start_x + t * (self._end_x - self._start_x)
        y = self._start_y + t * (self._end_y - self._start_y)
        return x, y

    def add_vehicle(self, vehicle: "Vehicle") -> None:
        """Add a vehicle to the lane.

        Args:
            vehicle: The Vehicle instance to add.
        """
        if vehicle not in self._active_vehicles:
            self._active_vehicles.append(vehicle)

    def remove_vehicle(self, vehicle: "Vehicle") -> None:
        """Remove a vehicle from the lane.

        Args:
            vehicle: The Vehicle instance to remove.
        """
        if vehicle in self._active_vehicles:
            self._active_vehicles.remove(vehicle)

    def get_vehicles(self) -> List["Vehicle"]:
        """Get all active vehicles in this lane.

        Returns:
            List of active vehicles.
        """
        return list(self._active_vehicles)
