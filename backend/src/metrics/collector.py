from typing import Any, Dict, List

from src.vehicles.vehicle import Vehicle


class MetricCollector:
    """Collects and aggregates simulation metrics, filtering out pre-warmup records."""

    def __init__(
        self, update_frequency: float = 1.0, warmup_time: float = 30.0
    ) -> None:
        """Initialize the MetricCollector.

        Args:
            update_frequency: Frequency of metrics updates (Hz).
            warmup_time: Duration of warmup phase in seconds.

        Raises:
            ValueError: If parameters violate constraints.
        """
        if update_frequency <= 0:
            raise ValueError("update_frequency must be greater than zero.")
        if warmup_time < 0:
            raise ValueError("warmup_time cannot be negative.")

        self._update_frequency = update_frequency
        self._warmup_time = warmup_time

        self._update_interval = 1.0 / update_frequency
        self._time_since_last_update = 0.0

        # Stores time-series of collected metric snapshots
        self._history: List[Dict[str, Any]] = []

    @property
    def update_frequency(self) -> float:
        """Get the configured update frequency in Hz."""
        return self._update_frequency

    @property
    def warmup_time(self) -> float:
        """Get the configured warmup time in seconds."""
        return self._warmup_time

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Get the logged metrics history."""
        return list(self._history)

    def is_in_warmup(self, elapsed_time: float) -> bool:
        """Check if the given elapsed time is within the warmup period.

        Args:
            elapsed_time: Current simulation elapsed time in seconds.

        Returns:
            True if elapsed_time is less than warmup_time.
        """
        return elapsed_time < self._warmup_time

    def should_update(self, dt: float) -> bool:
        """Determine if enough time has passed to trigger a metrics update tick.

        Args:
            dt: Time step duration in seconds.

        Returns:
            True if a metrics tick should occur.
        """
        self._time_since_last_update += dt
        # Allow small floating-point threshold margin
        if self._time_since_last_update >= self._update_interval - 1e-6:
            self._time_since_last_update = 0.0
            return True
        return False

    def get_valid_vehicles(self, vehicles: List[Vehicle]) -> List[Vehicle]:
        """Filter out vehicles that spawned or exited during the warmup period.

        Args:
            vehicles: List of Vehicle objects.

        Returns:
            Filtered list of Vehicle objects spawned and exited after warmup.
        """
        valid: List[Vehicle] = []
        for v in vehicles:
            if v.spawn_time is None or v.spawn_time < self._warmup_time:
                continue
            if v.exit_time is not None and v.exit_time < self._warmup_time:
                continue
            valid.append(v)
        return valid

    def update(
        self,
        dt: float,
        elapsed_time: float,
        active_vehicles: List[Vehicle],
        exited_vehicles: List[Vehicle],
    ) -> None:
        """Tick the collector, updating metrics if update interval is reached.

        If elapsed_time is below warmup_time, the tick is ignored for metric collection.

        Args:
            dt: Time step duration in seconds.
            elapsed_time: Current simulation elapsed time in seconds.
            active_vehicles: List of currently active vehicles.
            exited_vehicles: List of exited vehicles.
        """
        if not self.should_update(dt):
            return

        if self.is_in_warmup(elapsed_time):
            return

        # Filter valid vehicles (post-warmup only)
        valid_active = self.get_valid_vehicles(active_vehicles)
        valid_exited = self.get_valid_vehicles(exited_vehicles)

        # Log metrics to history
        snapshot = self._compute_tick_metrics(elapsed_time, valid_active, valid_exited)
        self._history.append(snapshot)

    def _compute_tick_metrics(
        self,
        elapsed_time: float,
        active_vehicles: List[Vehicle],
        exited_vehicles: List[Vehicle],
    ) -> Dict[str, Any]:
        """Helper to construct a simple metrics snapshot dictionary.

        This acts as a placeholder database structure to be populated/extended by
        specific metric calculators in subsequent issues.
        """
        return {
            "time": elapsed_time,
            "active_count": len(active_vehicles),
            "exited_count": len(exited_vehicles),
        }

    def reset(self) -> None:
        """Reset the metrics collector state."""
        self._time_since_last_update = 0.0
        self._history.clear()
