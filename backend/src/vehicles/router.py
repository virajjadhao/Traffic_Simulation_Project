from typing import Dict, Optional, Tuple

from src.core.enums import Direction, VehicleState
from src.roads.lane import Lane
from src.vehicles.vehicle import Vehicle


class VirtualVehicle:
    """A virtual stationary vehicle representing a stop line or barrier."""

    def __init__(self, vehicle_id: str, position: float, lane: Lane) -> None:
        self.vehicle_id = vehicle_id
        self.position = position
        self.lane = lane
        self.speed = 0.0
        self.length = 0.0  # Zero physical length for virtual stop line points
        self.width = 0.0
        self.state = VehicleState.WAITING

    @property
    def coords(self) -> Tuple[float, float]:
        return self.lane.get_point_at_distance(self.position)


def find_leader(
    vehicle: Vehicle,
    traffic_signals: Optional[Dict[Direction, bool]] = None,
) -> Tuple[Optional[Vehicle | VirtualVehicle], float]:
    """Find the leading vehicle or obstacle in front of the vehicle along its route.

    Args:
        vehicle: The subject vehicle.
        traffic_signals: Dict mapping Direction to a boolean indicating if green
          (True=green, False=red).

    Returns:
        A tuple of (leading_vehicle_or_obstacle, gap_distance).
        If no obstacle is found, returns (None, float('inf')).
    """
    if vehicle.state == VehicleState.EXITED:
        return None, float("inf")

    route = vehicle.route
    current_lane_idx = vehicle.current_lane_index

    # 1. Check current lane
    current_lane = route[current_lane_idx]
    vehicles_in_lane = current_lane.get_vehicles()

    # Sort vehicles in lane by position ascending
    sorted_vehicles = sorted(vehicles_in_lane, key=lambda v: v.position)

    # Find vehicles in front on the same lane
    idx = sorted_vehicles.index(vehicle)
    same_lane_leader = None
    for v in sorted_vehicles[idx + 1 :]:
        if v.state != VehicleState.EXITED:
            same_lane_leader = v
            break

    if same_lane_leader is not None:
        # Gap is distance between front of subject and rear of leader
        gap = (
            same_lane_leader.position - same_lane_leader.length / 2.0
        ) - (vehicle.position + vehicle.length / 2.0)
        return same_lane_leader, max(0.0, gap)

    # 2. If no leader in current lane, check traffic signals stop lines
    # Stop line is at the end of the incoming lane (index 0 of route)
    if current_lane_idx == 0:
        # Check traffic signal state for this direction
        # If signal is Red (False), insert a virtual stationary leader
        incoming_direction = current_lane.lane_id.split("_")[0]
        dir_map = {
            "n": Direction.NORTH,
            "s": Direction.SOUTH,
            "e": Direction.EAST,
            "w": Direction.WEST,
        }
        direction = dir_map.get(incoming_direction)

        if direction is not None and traffic_signals is not None:
            is_green = traffic_signals.get(direction, True)
            if not is_green:
                # Signal is RED: place a virtual leader at the end of incoming lane
                stop_line_pos = current_lane.length
                gap = stop_line_pos - (vehicle.position + vehicle.length / 2.0)
                virtual_leader = VirtualVehicle(
                    vehicle_id=f"stop_line_{direction.value}",
                    position=stop_line_pos,
                    lane=current_lane,
                )
                return virtual_leader, max(0.0, gap)

    # 3. Look ahead into subsequent lanes in the route
    accumulated_gap = current_lane.length - (
        vehicle.position + vehicle.length / 2.0
    )

    for next_lane_idx in range(current_lane_idx + 1, len(route)):
        next_lane = route[next_lane_idx]
        next_lane_vehicles = next_lane.get_vehicles()

        if next_lane_vehicles:
            # Find the closest vehicle on the next lane
            sorted_next = sorted(next_lane_vehicles, key=lambda v: v.position)
            closest_leader = None
            for v in sorted_next:
                if v.state != VehicleState.EXITED:
                    closest_leader = v
                    break

            if closest_leader is not None:
                gap = accumulated_gap + (
                    closest_leader.position - closest_leader.length / 2.0
                )
                return closest_leader, max(0.0, gap)

        # Accumulate the entire lane length for the next iteration
        accumulated_gap += next_lane.length

    return None, float("inf")
