from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


def calculate_travel_time_reliability(valid_exited: List[Vehicle]) -> Dict[str, Any]:
    """Calculate the Travel Time Reliability (Planning Time Index - PTI).

    PTI is the ratio of the 95th percentile travel time to the median travel time.
    """
    n = len(valid_exited)
    if n == 0:
        return {
            "value": 1.0,
            "unit": "dimensionless",
            "median_travel_time": 0.0,
            "p95_travel_time": 0.0,
        }

    travel_times: List[float] = []
    for v in valid_exited:
        if v.spawn_time is not None and v.exit_time is not None:
            travel_times.append(v.exit_time - v.spawn_time)

    if not travel_times:
        return {
            "value": 1.0,
            "unit": "dimensionless",
            "median_travel_time": 0.0,
            "p95_travel_time": 0.0,
        }

    sorted_tt = sorted(travel_times)
    m = len(sorted_tt)

    # 1. Compute Median (50th percentile)
    if m % 2 == 1:
        median = sorted_tt[m // 2]
    else:
        median = (sorted_tt[m // 2 - 1] + sorted_tt[m // 2]) / 2.0

    # 2. Compute 95th percentile using nearest-rank
    idx = int(m * 0.95)
    idx = max(0, min(idx, m - 1))
    p95 = sorted_tt[idx]

    # 3. Compute PTI (handle edge cases)
    if median == 0.0:
        value = None
    else:
        value = p95 / median

    return {
        "value": value,
        "unit": "dimensionless",
        "median_travel_time": median,
        "p95_travel_time": p95,
    }
