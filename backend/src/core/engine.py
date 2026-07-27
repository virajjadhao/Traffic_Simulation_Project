import threading
import time
from typing import Callable, List, Optional

from src.core.clock import Clock
from src.core.enums import SimulationStatus


class SimulationEngine:
    """Orchestrates the simulation lifecycle and manages the tick loop execution."""

    def __init__(self, clock: Clock, duration: float = 300.0) -> None:
        """Initialize the SimulationEngine.

        Args:
            clock: The thread-safe simulation clock.
            duration: Total duration of the simulation in seconds.

        Raises:
            ValueError: If duration is less than or equal to zero.
        """
        if duration <= 0:
            raise ValueError("Simulation duration must be greater than zero.")

        self._clock: Clock = clock
        self._duration: float = duration
        self._status: SimulationStatus = SimulationStatus.INITIALIZED
        self._lock: threading.Lock = threading.Lock()

        # Callbacks
        self._tick_callbacks: List[Callable[[], None]] = []
        self._status_callbacks: List[Callable[[SimulationStatus], None]] = []

        # Thread management
        self._thread: Optional[threading.Thread] = None

    @property
    def status(self) -> SimulationStatus:
        """Get the current simulation lifecycle status."""
        with self._lock:
            return self._status

    @property
    def duration(self) -> float:
        """Get the total duration of the simulation in seconds."""
        return self._duration

    def register_tick_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be executed on every simulation tick."""
        with self._lock:
            self._tick_callbacks.append(callback)

    def register_status_callback(
        self, callback: Callable[[SimulationStatus], None]
    ) -> None:
        """Register a callback to be executed on status transitions."""
        with self._lock:
            self._status_callbacks.append(callback)

    def start(self) -> None:
        """Start the simulation loop from INITIALIZED state.

        Raises:
            RuntimeError: If the simulation is not in INITIALIZED state.
        """
        with self._lock:
            if self._status != SimulationStatus.INITIALIZED:
                raise RuntimeError(
                    f"Cannot start simulation from '{self._status.value}' status. "
                    "Must be in 'initialized' status."
                )
            self._status = SimulationStatus.RUNNING
            self._trigger_status_callbacks()
            self._spawn_loop_thread()

    def pause(self) -> None:
        """Pause the running simulation.

        Raises:
            RuntimeError: If the simulation is not currently running.
        """
        with self._lock:
            if self._status != SimulationStatus.RUNNING:
                raise RuntimeError(
                    f"Cannot pause simulation from '{self._status.value}' status. "
                    "Must be in 'running' status."
                )
            self._status = SimulationStatus.PAUSED
            self._trigger_status_callbacks()

    def resume(self) -> None:
        """Resume a paused simulation.

        Raises:
            RuntimeError: If the simulation is not currently paused.
        """
        with self._lock:
            if self._status != SimulationStatus.PAUSED:
                raise RuntimeError(
                    f"Cannot resume simulation from '{self._status.value}' status. "
                    "Must be in 'paused' status."
                )
            self._status = SimulationStatus.RUNNING
            self._trigger_status_callbacks()
            self._spawn_loop_thread()

    def stop(self) -> None:
        """Force terminate the simulation, transitioning to COMPLETED status."""
        with self._lock:
            if self._status == SimulationStatus.COMPLETED:
                return
            self._status = SimulationStatus.COMPLETED
            self._trigger_status_callbacks()

    def reset(self) -> None:
        """Reset the simulation back to INITIALIZED status."""
        with self._lock:
            self._status = SimulationStatus.INITIALIZED
            self._clock.reset()
            self._trigger_status_callbacks()

    def step(self) -> None:
        """Manually execute a single tick.

        Can only be called in INITIALIZED or PAUSED status.

        Raises:
            RuntimeError: If called while simulation is running or completed.
        """
        with self._lock:
            if self._status in (SimulationStatus.RUNNING, SimulationStatus.COMPLETED):
                raise RuntimeError(
                    f"Cannot step simulation in '{self._status.value}' status."
                )
            self._execute_tick()

    def _spawn_loop_thread(self) -> None:
        """Spawns the background simulation runner thread."""
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        """Tick runner loop running on a background thread."""
        dt = self._clock.time_step
        while True:
            with self._lock:
                if self._status != SimulationStatus.RUNNING:
                    break
                self._execute_tick()
                if self._status == SimulationStatus.COMPLETED:  # type: ignore[comparison-overlap]
                    break
            time.sleep(dt)

    def _execute_tick(self) -> None:
        """Execute the logic for a single tick (clock increment & callbacks)."""
        self._clock.tick()
        for callback in self._tick_callbacks:
            callback()

        # Check completion condition
        if self._clock.get_elapsed_time() >= self._duration:
            self._status = SimulationStatus.COMPLETED
            self._trigger_status_callbacks()

    def _trigger_status_callbacks(self) -> None:
        """Trigger all registered status change callbacks."""
        for callback in self._status_callbacks:
            callback(self._status)
