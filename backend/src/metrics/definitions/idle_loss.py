from typing import Any, Dict, List


class IdleOpportunityLossTracker:
    """Tracks idle opportunity loss (IOL) for fixed-time traffic signals."""

    def __init__(self) -> None:
        """Initialize the IdleOpportunityLossTracker."""
        self._iol_ticks = 0
        self._total_ticks = 0

    def record_tick(
        self,
        controller_type: str,
        signals: List[Dict[str, str]],
        queue_lengths: Dict[str, int],
    ) -> bool:
        """Record a single tick and update IOL stats.

        For roundabouts, IOL is always 0.0.

        Args:
            controller_type: Type name of the active controller.
            signals: List of signal head dictionaries.
            queue_lengths: Dictionary of queue lengths per direction.

        Returns:
            True if this tick was classified as an IOL tick.
        """
        if controller_type != "fixed_time_signal":
            self._total_ticks += 1
            return False

        # Find green and red approaches
        green_dirs = [s["direction"] for s in signals if s["color"] == "green"]
        red_dirs = [s["direction"] for s in signals if s["color"] == "red"]

        has_waiting_in_red = any(queue_lengths.get(d, 0) > 0 for d in red_dirs)
        no_vehicles_in_green = all(queue_lengths.get(d, 0) == 0 for d in green_dirs)

        is_idle = has_waiting_in_red and no_vehicles_in_green
        if is_idle:
            self._iol_ticks += 1

        self._total_ticks += 1
        return is_idle

    def calculate_metric(self) -> Dict[str, Any]:
        """Compute the idle opportunity loss metric.

        Returns:
            A dictionary matching the metrics schema.
        """
        if self._total_ticks == 0:
            value = 0.0
        else:
            value = self._iol_ticks / self._total_ticks

        return {
            "value": value,
            "unit": "dimensionless",
        }

    def reset(self) -> None:
        """Reset the tracker history."""
        self._iol_ticks = 0
        self._total_ticks = 0
