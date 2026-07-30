from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


def calculate_average_wait_time(valid_exited: List[Vehicle]) -> Dict[str, Any]:
    """Calculate the average wait time of vehicles that have exited the simulation.

    Args:
        valid_exited: Exited vehicles that passed warmup filtering.

    Returns:
        A dictionary containing the calculated value, unit, sample size, and confidence.
    """
    n = len(valid_exited)
    if n == 0:
        return {
            "value": 0.0,
            "unit": "seconds",
            "sampleSize": 0,
            "confidence": "low",
        }

    total_wait_time = sum(v.wait_time for v in valid_exited)
    value = total_wait_time / n
    confidence = "low" if n < 10 else "high"

    return {
        "value": value,
        "unit": "seconds",
        "sampleSize": n,
        "confidence": confidence,
    }
