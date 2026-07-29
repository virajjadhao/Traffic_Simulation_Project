import math
from typing import Any, Dict, List

from src.controllers.base import BaseController
from src.core.enums import Direction, VehicleState
from src.vehicles.vehicle import Vehicle


class RoundaboutController(BaseController):
    """Modern roundabout intersection controller strategy."""

    def __init__(
        self,
        inner_radius: float = 10.0,
        outer_radius: float = 20.0,
        circulating_lanes: int = 1,
        critical_gap: float = 4.0,
        follow_up_time: float = 2.5,
        entry_speed: float = 5.0,
        circulating_speed: float = 8.0,
    ) -> None:
        """Initialize the RoundaboutController.

        Args:
            inner_radius: Inner radius of the roundabout (meters).
            outer_radius: Outer radius of the roundabout (meters).
            circulating_lanes: Number of circulating lanes.
            critical_gap: Minimum safe time gap to enter (seconds).
            follow_up_time: Time between successive entries (seconds).
            entry_speed: Max speed at entry (m/s).

        Raises:
            ValueError: If configuration values violate boundary constraints.
        """
        if inner_radius <= 5 or inner_radius > 50:
            raise ValueError("inner_radius must be in (5, 50].")
        if outer_radius <= inner_radius:
            raise ValueError("outer_radius must be greater than inner_radius.")
        if circulating_lanes < 1 or circulating_lanes > 3:
            raise ValueError("circulating_lanes must be in [1, 3].")
        if critical_gap <= 0 or critical_gap > 10:
            raise ValueError("critical_gap must be in (0, 10].")
        if follow_up_time <= 0:
            raise ValueError("follow_up_time must be positive.")
        if entry_speed <= 0:
            raise ValueError("entry_speed must be positive.")
        if circulating_speed <= 0 or circulating_speed > 15:
            raise ValueError("circulating_speed must be in (0, 15].")

        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._circulating_lanes = circulating_lanes
        self._critical_gap = critical_gap
        self._follow_up_time = follow_up_time
        self._entry_speed = entry_speed
        self._circulating_speed = circulating_speed

        self._time_elapsed = 0.0
        self._circulating_count = 0

        self.yield_signals: Dict[Direction, bool] = {
            Direction.NORTH: True,
            Direction.SOUTH: True,
            Direction.EAST: True,
            Direction.WEST: True,
        }

    def update(self, delta_time: float, active_vehicles: List[Vehicle]) -> None:
        """Update the roundabout controller decisions based on circulating traffic.

        Args:
            delta_time: Elapsed time in seconds.
            active_vehicles: List of all active vehicles.
        """
        if delta_time <= 0:
            return

        self._time_elapsed += delta_time

        # Update vehicle overrides and states first
        for v in active_vehicles:
            if v.current_lane_index == 1:
                v.state = VehicleState.IN_ROUNDABOUT

                # Check if it's a real vehicle with route and position
                if hasattr(v, "route") and hasattr(v, "position"):
                    # Circulating coordinates override
                    conn_lane = v.route[1]
                    l_conn = conn_lane.length
                    p = max(0.0, min(1.0, v.position / l_conn))

                    start_x, start_y = conn_lane.start_coords
                    end_x, end_y = conn_lane.end_coords

                    theta_start = math.atan2(start_y, start_x)
                    theta_end = math.atan2(end_y, end_x)

                    # Traffic in roundabout moves counter-clockwise (increasing angle)
                    delta_theta = (theta_end - theta_start) % (2 * math.pi)
                    theta = theta_start + p * delta_theta

                    r_start = math.sqrt(start_x**2 + start_y**2)
                    r_end = math.sqrt(end_x**2 + end_y**2)
                    r = r_start + p * (r_end - r_start)

                    x = r * math.cos(theta)
                    y = r * math.sin(theta)

                    v.coords_override = (x, y)

                    # Heading override (circular tangent heading)
                    dx = -math.sin(theta)
                    dy = math.cos(theta)
                    v.heading_override = math.degrees(math.atan2(dx, dy)) % 360.0

                    # Speed limit override
                    v.speed_limit_override = self._circulating_speed
            else:
                # Clear overrides for vehicles not in the roundabout circle
                if hasattr(v, "coords_override"):
                    v.coords_override = None
                if hasattr(v, "heading_override"):
                    v.heading_override = None
                if hasattr(v, "speed_limit_override"):
                    v.speed_limit_override = None
                if v.state == VehicleState.IN_ROUNDABOUT:
                    v.state = VehicleState.APPROACHING

        # Identify circulating vehicles:
        # Currently on connection lane (index 1) or state is IN_ROUNDABOUT
        circulating = [
            v
            for v in active_vehicles
            if v.current_lane_index == 1 or v.state == VehicleState.IN_ROUNDABOUT
        ]
        self._circulating_count = len(circulating)

        # Define entry angles
        entry_angles = {
            Direction.EAST: 0.0,
            Direction.NORTH: math.pi / 2,
            Direction.WEST: math.pi,
            Direction.SOUTH: -math.pi / 2,
        }

        # For each incoming approach direction, check oncoming circulating vehicles
        for direction, entry_angle in entry_angles.items():
            safe = True
            for v_circ in circulating:
                # Calculate circulating vehicle coordinates relative to center
                x, y = v_circ.coords
                theta_v = math.atan2(y, x)

                # Angular distance from circulating vehicle to entry point
                # (counter-clockwise)
                delta_theta = (entry_angle - theta_v) % (2 * math.pi)

                # Yield sector is the quadrant before the entry point:
                # delta_theta in [0, pi/2]
                if 0.0 <= delta_theta <= math.pi / 2:
                    # Compute linear distance along average radius
                    r = math.sqrt(x**2 + y**2)
                    dist = delta_theta * r

                    # Calculate time gap
                    if v_circ.speed > 0.5:
                        gap_time = dist / v_circ.speed
                    else:
                        # Stationary vehicle close to yield line is unsafe
                        gap_time = 0.0 if dist < 15.0 else float("inf")

                    if gap_time < self._critical_gap:
                        safe = False
                        break

            self.yield_signals[direction] = safe

    def get_state(self) -> Dict[str, Any]:
        """Get the snapshot state of the controller.

        Returns:
            ControllerState dictionary conforming to roundabout contract schema.
        """
        return {
            "type": "roundabout",
            "timeInCurrentState": self._time_elapsed,
            "innerRadius": self._inner_radius,
            "outerRadius": self._outer_radius,
            "circulatingCount": self._circulating_count,
        }

    def reset(self) -> None:
        """Reset the controller to its initial state."""
        self._time_elapsed = 0.0
        self._circulating_count = 0
        self.yield_signals = {
            Direction.NORTH: True,
            Direction.SOUTH: True,
            Direction.EAST: True,
            Direction.WEST: True,
        }
