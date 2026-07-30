from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


def get_vehicle_origin_direction(vehicle: Vehicle) -> str:
    """Helper to map a vehicle's origin lane to its direction string."""
    if not vehicle.route:
        return "unknown"
    first_lane_id = vehicle.route[0].lane_id.lower()
    prefix = first_lane_id.split("_")[0]
    if prefix.startswith("n"):
        return "north"
    elif prefix.startswith("s"):
        return "south"
    elif prefix.startswith("e"):
        return "east"
    elif prefix.startswith("w"):
        return "west"
    return "unknown"


def calculate_directional_fairness(valid_exited: List[Vehicle]) -> Dict[str, Any]:
    """Calculate Jain's Fairness Index across average wait times per direction.

    Jain's index = (sum(x_i))^2 / (n * sum(x_i^2))
    where x_i is the average wait time of exited vehicles from direction i.
    """
    # 1. Group wait times of exited vehicles by origin direction
    dir_wait_times: Dict[str, List[float]] = {
        "north": [],
        "south": [],
        "east": [],
        "west": [],
    }

    for v in valid_exited:
        dir_str = get_vehicle_origin_direction(v)
        if dir_str in dir_wait_times:
            dir_wait_times[dir_str].append(v.wait_time)

    # 2. Compute average wait time per direction
    per_direction: Dict[str, float] = {}
    for d, waits in dir_wait_times.items():
        if waits:
            per_direction[d] = sum(waits) / len(waits)

    # 3. Calculate Jain's Fairness Index across the included directions
    x = list(per_direction.values())
    n = len(x)

    if n == 0:
        value = 1.0
    else:
        sum_x = sum(x)
        sum_x_sq = sum(val**2 for val in x)
        if sum_x_sq == 0.0:
            value = 1.0
        else:
            value = (sum_x**2) / (n * sum_x_sq)

    # 4. Format per-direction wait times output (defaulting to 0.0 if empty)
    per_direction_output = {}
    for d in ["north", "south", "east", "west"]:
        waits = dir_wait_times[d]
        per_direction_output[d] = sum(waits) / len(waits) if waits else 0.0

    return {
        "value": value,
        "unit": "dimensionless",
        "perDirection": per_direction_output,
    }
