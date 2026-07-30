from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


def calculate_throughput(
    valid_exited: List[Vehicle],
    elapsed_time: float,
    warmup_time: float,
    window_size: float = 60.0,
) -> Dict[str, Any]:
    """Calculate total throughput and rolling throughput rate.

    Args:
        valid_exited: Exited vehicles that passed warmup filtering.
        elapsed_time: Current simulation elapsed time in seconds.
        warmup_time: Duration of the warmup phase in seconds.
        window_size: Rolling window size in seconds (default 60s).

    Returns:
        A dictionary containing the value, unit, rate, and rateUnit.
    """
    total_count = len(valid_exited)

    # 1. Determine active window boundaries
    t_start = max(warmup_time, elapsed_time - window_size)
    dt_window = elapsed_time - t_start

    # 2. Count exited vehicles within the active window
    window_count = sum(
        1
        for v in valid_exited
        if v.exit_time is not None and t_start <= v.exit_time <= elapsed_time
    )

    # 3. Compute rolling rate (vehicles per minute)
    if dt_window > 0.0:
        rate = (window_count / dt_window) * 60.0
    else:
        rate = 0.0

    return {
        "value": total_count,
        "unit": "vehicles",
        "rate": rate,
        "rateUnit": "vehicles_per_minute",
    }
