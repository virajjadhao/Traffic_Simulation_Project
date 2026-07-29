import math
from typing import Dict, Tuple


class IntersectionGeometry:
    """Defines spatial bounds and manages approach-to-exit lane mappings."""

    def __init__(self, center: Tuple[float, float], radius: float) -> None:
        """Initialize the IntersectionGeometry.

        Args:
            center: Coordinate pair (x, y) representing the center in meters.
            radius: Bounding circle radius of the intersection in meters.

        Raises:
            ValueError: If radius is less than or equal to zero.
        """
        if radius <= 0:
            raise ValueError("Bounding radius must be greater than zero.")

        self._center: Tuple[float, float] = center
        self._radius: float = radius

        # Maps incoming approach lane_id -> crossing start coordinates (x, y)
        self._approach_lanes: Dict[str, Tuple[float, float]] = {}

        # Maps crossing end coordinates (x, y) -> outgoing exit lane_id
        # We store keys as rounded coordinate tuples to prevent float
        # representation lookup misses.
        self._exit_lanes: Dict[Tuple[float, float], str] = {}

    @property
    def center(self) -> Tuple[float, float]:
        """Get the center coordinates of the intersection (x, y)."""
        return self._center

    @property
    def radius(self) -> float:
        """Get the bounding radius of the intersection."""
        return self._radius

    def is_within_intersection(self, x: float, y: float) -> bool:
        """Check if a coordinate (x, y) lies within the intersection's bounding circle.

        Args:
            x: X-coordinate in meters.
            y: Y-coordinate in meters.

        Returns:
            True if coordinates are within the bounding radius, else False.
        """
        return math.hypot(x - self._center[0], y - self._center[1]) <= self._radius

    def _round_coords(self, coords: Tuple[float, float]) -> Tuple[float, float]:
        """Round coordinates to 6 decimal places to prevent floating point key mismatch.

        Args:
            coords: A tuple of (x, y) coordinates.

        Returns:
            A tuple of (x, y) coordinates rounded to 6 decimal places.
        """
        return round(coords[0], 6), round(coords[1], 6)

    def map_approach_lane(
        self, lane_id: str, crossing_start: Tuple[float, float]
    ) -> None:
        """Map an incoming approach lane to its entering crossing start point.

        Args:
            lane_id: Unique identifier for the incoming lane.
            crossing_start: Coordinates (x, y) where the lane enters the intersection.
        """
        self._approach_lanes[lane_id] = crossing_start

    def map_exit_lane(self, crossing_end: Tuple[float, float], lane_id: str) -> None:
        """Map a crossing end point to an outgoing exit lane.

        Args:
            crossing_end: Coordinates (x, y) where connection exits.
            lane_id: Unique identifier for the outgoing lane.
        """
        rounded = self._round_coords(crossing_end)
        self._exit_lanes[rounded] = lane_id

    def get_crossing_start(self, lane_id: str) -> Tuple[float, float]:
        """Get the entering crossing start coordinates for an incoming lane.

        Args:
            lane_id: Unique identifier of the incoming approach lane.

        Returns:
            Tuple of (x, y) coordinates.

        Raises:
            KeyError: If the lane_id is not registered.
        """
        if lane_id not in self._approach_lanes:
            raise KeyError(f"Approach lane '{lane_id}' is not mapped.")
        return self._approach_lanes[lane_id]

    def get_exit_lane(self, crossing_end: Tuple[float, float]) -> str:
        """Get the outgoing exit lane ID starting at the given coordinates.

        Args:
            crossing_end: Tuple of (x, y) coordinates.

        Returns:
            Unique identifier of the outgoing lane.

        Raises:
            KeyError: If no exit lane starts at the given coordinates.
        """
        rounded = self._round_coords(crossing_end)
        if rounded not in self._exit_lanes:
            raise KeyError(f"No exit lane mapped for coordinates {crossing_end}.")
        return self._exit_lanes[rounded]
