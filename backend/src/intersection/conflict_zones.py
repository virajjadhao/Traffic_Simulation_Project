import math
from typing import List, Optional, Tuple

from src.core.enums import VehicleState
from src.vehicles.vehicle import Vehicle


class ConflictZoneDetector:
    """Detects and calculates safety gaps for intersecting vehicle paths."""

    def __init__(self, safety_buffer: float = 2.0) -> None:
        """Initialize the ConflictZoneDetector.

        Args:
            safety_buffer: Safety distance buffer (meters) to maintain.

        Raises:
            ValueError: If safety_buffer is negative.
        """
        if safety_buffer < 0:
            raise ValueError("Safety buffer cannot be negative.")
        self._safety_buffer = safety_buffer

    def _find_intersection(
        self,
        a: Tuple[float, float],
        b: Tuple[float, float],
        c: Tuple[float, float],
        d: Tuple[float, float],
    ) -> Optional[Tuple[float, float]]:
        """Find the intersection point of line segments ab and cd.

        Args:
            a: Start coordinates (x, y) of segment ab.
            b: End coordinates (x, y) of segment ab.
            c: Start coordinates (x, y) of segment cd.
            d: End coordinates (x, y) of segment cd.

        Returns:
            The intersection point (x, y) if segments intersect, else None.
        """
        dx1, dy1 = b[0] - a[0], b[1] - a[1]
        dx2, dy2 = d[0] - c[0], d[1] - c[1]

        det = dx2 * dy1 - dx1 * dy2
        if abs(det) < 1e-9:
            return None  # Parallel or collinear

        num_t = (a[0] - c[0]) * dy2 - (a[1] - c[1]) * dx2
        num_u = (c[1] - a[1]) * dx1 - (c[0] - a[0]) * dy1

        t = num_t / det
        u = num_u / det

        eps = 1e-6
        if -eps <= t <= 1.0 + eps and -eps <= u <= 1.0 + eps:
            t = max(0.0, min(1.0, t))
            x = a[0] + t * dx1
            y = a[1] + t * dy1
            return x, y

        return None

    def check_conflicts(
        self, vehicle: Vehicle, active_vehicles: List[Vehicle]
    ) -> float:
        """Check for conflicts and return safety gap to the nearest competitor.

        Args:
            vehicle: The subject vehicle.
            active_vehicles: List of all active vehicles.

        Returns:
            Safety gap in meters, or float('inf') if no yield is needed.
        """
        if vehicle.state == VehicleState.EXITED:
            return float("inf")

        route = vehicle.route
        if vehicle.current_lane_index >= 2 or len(route) < 3:
            return float("inf")

        subj_conn = route[1]
        a, b = subj_conn.start_coords, subj_conn.end_coords

        min_gap = float("inf")

        for other in active_vehicles:
            if other.vehicle_id == vehicle.vehicle_id:
                continue

            if other.state == VehicleState.EXITED:
                continue

            if other.current_lane_index >= 2:
                continue

            other_route = other.route
            if len(other_route) < 3:
                continue

            other_conn = other_route[1]
            if subj_conn.lane_id == other_conn.lane_id:
                continue

            c, d = other_conn.start_coords, other_conn.end_coords

            intersection = self._find_intersection(a, b, c, d)
            if intersection is None:
                continue

            s_subj = math.hypot(intersection[0] - a[0], intersection[1] - a[1])
            s_other = math.hypot(intersection[0] - c[0], intersection[1] - c[1])

            if vehicle.current_lane_index == 0:
                dist_subj = (route[0].length - vehicle.position) + s_subj
            else:
                dist_subj = s_subj - vehicle.position

            if other.current_lane_index == 0:
                dist_other = (other_route[0].length - other.position) + s_other
            else:
                dist_other = s_other - other.position

            if dist_subj < -vehicle.length / 2.0:
                continue

            if dist_other < -other.length / 2.0:
                continue

            is_other_occupying = -other.length / 2.0 <= dist_other <= other.length / 2.0
            is_subj_occupying = (
                -vehicle.length / 2.0 <= dist_subj <= vehicle.length / 2.0
            )

            other_has_priority = False

            if is_other_occupying and not is_subj_occupying:
                other_has_priority = True
            elif is_subj_occupying and not is_other_occupying:
                other_has_priority = False
            elif is_subj_occupying and is_other_occupying:
                other_has_priority = dist_other < dist_subj
            else:
                if dist_other < dist_subj:
                    other_has_priority = True
                elif dist_other == dist_subj:
                    other_has_priority = other.vehicle_id < vehicle.vehicle_id

            if other_has_priority:
                gap = dist_subj - (vehicle.length / 2.0) - self._safety_buffer
                gap = max(0.0, gap)
                if gap < min_gap:
                    min_gap = gap

        return min_gap
