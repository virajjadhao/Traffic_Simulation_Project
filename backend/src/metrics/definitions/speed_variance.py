import math
from typing import Any, Dict, List, Optional

from src.vehicles.vehicle import Vehicle


def calculate_active_cv(active_vehicles: List[Vehicle]) -> Optional[float]:
    """Calculate the speed Coefficient of Variation (CV) for active vehicles at a tick.

    If fewer than 2 vehicles are active, returns None (to skip this tick).
    """
    n = len(active_vehicles)
    if n < 2:
        return None

    speeds = [v.speed for v in active_vehicles]
    mean_speed = sum(speeds) / n

    if mean_speed == 0.0:
        return 0.0

    variance = sum((s - mean_speed) ** 2 for s in speeds) / n
    std_dev = math.sqrt(variance)

    return std_dev / mean_speed


def calculate_speed_variance_index(cv_history: List[float]) -> Dict[str, Any]:
    """Calculate the Speed Variance Index (SVI) over the simulation history."""
    valid_cvs = [cv for cv in cv_history if cv is not None]
    if not valid_cvs:
        return {
            "value": 0.0,
            "unit": "dimensionless",
        }

    value = sum(valid_cvs) / len(valid_cvs)

    return {
        "value": value,
        "unit": "dimensionless",
    }
