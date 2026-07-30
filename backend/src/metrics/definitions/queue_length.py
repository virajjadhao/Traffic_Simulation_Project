from typing import Any, Dict, List

from src.core.enums import Direction
from src.roads.network import RoadNetwork


class QueueLengthTracker:
    """Tracks queue lengths per direction and computes summary statistics."""

    def __init__(self, wait_speed_threshold: float = 0.5) -> None:
        """Initialize the QueueLengthTracker.

        Args:
            wait_speed_threshold: Speed threshold below which a vehicle is queued.
        """
        self._wait_speed_threshold = wait_speed_threshold
        # Stores lists of queue lengths per tick post-warmup
        self._history: Dict[str, List[int]] = {
            "north": [],
            "south": [],
            "east": [],
            "west": [],
        }

    @property
    def wait_speed_threshold(self) -> float:
        """Get the wait speed threshold in m/s."""
        return self._wait_speed_threshold

    def record_tick(self, network: RoadNetwork) -> Dict[str, int]:
        """Measure current queue lengths per approach and log to history.

        Args:
            network: The RoadNetwork instance.

        Returns:
            A dict mapping each direction to its instantaneous queue length.
        """
        current: Dict[str, int] = {}
        for d in Direction:
            direction_str = d.value
            approach = network.get_incoming_approach(d)
            queue_count = sum(
                1
                for v in approach.get_active_vehicles()
                if v.speed < self._wait_speed_threshold
            )
            current[direction_str] = queue_count
            self._history[direction_str].append(queue_count)
        return current

    def calculate_statistics(self) -> Dict[str, Any]:
        """Compute the final queue length statistics across history.

        Returns:
            A dictionary conforming to the queue_length metrics schema.
        """
        per_direction: Dict[str, Dict[str, Any]] = {}
        all_samples: List[int] = []

        for direction_str in ["north", "south", "east", "west"]:
            history = self._history[direction_str]
            if history:
                avg_val = sum(history) / len(history)
                max_val = max(history)
                all_samples.extend(history)
            else:
                avg_val = 0.0
                max_val = 0

            per_direction[direction_str] = {
                "average": avg_val,
                "maximum": max_val,
            }

        if all_samples:
            max_global = max(all_samples)
            # 95th percentile using nearest-rank method
            sorted_samples = sorted(all_samples)
            idx = int(len(sorted_samples) * 0.95)
            idx = max(0, min(idx, len(sorted_samples) - 1))
            p95_global = sorted_samples[idx]
        else:
            max_global = 0
            p95_global = 0

        # Global average is the mean of the 4 approach averages (from contract formula)
        avg_global = sum(per_direction[d]["average"] for d in per_direction) / 4.0

        return {
            "average": avg_global,
            "maximum": max_global,
            "percentile95": p95_global,
            "unit": "vehicles",
            "perDirection": per_direction,
        }

    def reset(self) -> None:
        """Reset the queue length tracker history."""
        for d in self._history:
            self._history[d].clear()
