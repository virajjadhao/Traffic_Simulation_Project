from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


def calculate_stop_count(valid_exited: List[Vehicle]) -> Dict[str, Any]:
    """Calculate the average stop count and total stops of exited vehicles.

    Args:
        valid_exited: Exited vehicles that passed warmup filtering.

    Returns:
        A dictionary containing the value, unit, and total stops.
    """
    n = len(valid_exited)
    if n == 0:
        return {
            "value": 0.0,
            "unit": "stops_per_vehicle",
            "total": 0,
        }

    total_stops = sum(v.stop_count for v in valid_exited)
    value = total_stops / n

    return {
        "value": value,
        "unit": "stops_per_vehicle",
        "total": total_stops,
    }
