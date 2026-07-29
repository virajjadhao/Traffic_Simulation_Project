import threading


class Clock:
    """Thread-safe simulation clock managing discrete time steps.

    The clock advances by a constant time step (dt) on each tick.
    """

    def __init__(self, time_step: float = 0.1) -> None:
        """Initialize the Clock.

        Args:
            time_step: The duration of a single tick in seconds (dt).

        Raises:
            ValueError: If time_step is less than or equal to zero.
        """
        if time_step <= 0:
            raise ValueError("Time step must be positive and non-zero.")
        self._time_step: float = time_step
        self._ticks: int = 0
        self._lock: threading.Lock = threading.Lock()

    def tick(self) -> None:
        """Advance the simulation clock by one tick (dt)."""
        with self._lock:
            self._ticks += 1

    def reset(self) -> None:
        """Reset the clock ticks to zero."""
        with self._lock:
            self._ticks = 0

    @property
    def time_step(self) -> float:
        """Get the duration of a single tick (dt) in seconds."""
        return self._time_step

    def get_tick_count(self) -> int:
        """Get the total number of elapsed ticks.

        Returns:
            The total ticks elapsed since initialization or last reset.
        """
        with self._lock:
            return self._ticks

    def get_elapsed_time(self) -> float:
        """Get the total elapsed simulation time in seconds.

        Returns:
            Elapsed time in seconds.
        """
        with self._lock:
            return self._ticks * self._time_step

    def seconds_to_ticks(self, seconds: float) -> int:
        """Convert a duration in seconds to simulation ticks.

        Args:
            seconds: The duration in seconds.

        Returns:
            The equivalent number of ticks (rounded to nearest integer).

        Raises:
            ValueError: If seconds is negative.
        """
        if seconds < 0:
            raise ValueError("Seconds cannot be negative.")
        import math

        return math.floor(seconds / self._time_step + 0.5)

    def ticks_to_seconds(self, ticks: int) -> float:
        """Convert a count of ticks to simulation seconds.

        Args:
            ticks: The number of simulation ticks.

        Returns:
            The equivalent duration in seconds.

        Raises:
            ValueError: If ticks is negative.
        """
        if ticks < 0:
            raise ValueError("Ticks cannot be negative.")
        return ticks * self._time_step
