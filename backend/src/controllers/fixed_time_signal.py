from typing import Any, Dict, List, Optional

from src.controllers.base import BaseController
from src.vehicles.vehicle import Vehicle


class FixedTimeSignalController(BaseController):
    """Fixed-time traffic signal controller strategy."""

    VALID_PHASES = {
        "ns_green",
        "ns_yellow",
        "ew_green",
        "ew_yellow",
        "all_red",
    }

    def __init__(
        self,
        green_time: float = 30.0,
        yellow_time: float = 4.0,
        all_red_time: float = 2.0,
        phase_sequence: Optional[List[str]] = None,
        offset: float = 0.0,
    ) -> None:
        """Initialize the FixedTimeSignalController.

        Args:
            green_time: Duration of the green phase (seconds).
            yellow_time: Duration of the yellow phase (seconds).
            all_red_time: Duration of the all-red clearance phase (seconds).
            phase_sequence: Ordered sequence of phase names.
            offset: Timing offset applied at start of simulation (seconds).

        Raises:
            ValueError: If duration parameters are invalid, or if the phase
                sequence contains invalid phase names.
        """
        if green_time <= 0 or yellow_time <= 0:
            raise ValueError("Green and yellow phase times must be positive.")
        if all_red_time < 0:
            raise ValueError("All-red phase time cannot be negative.")
        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        if phase_sequence is not None:
            self._phase_sequence = phase_sequence
        else:
            self._phase_sequence = [
                "ns_green",
                "ns_yellow",
                "all_red",
                "ew_green",
                "ew_yellow",
                "all_red",
            ]

        if not self._phase_sequence:
            raise ValueError("Phase sequence cannot be empty.")

        for phase in self._phase_sequence:
            if phase not in self.VALID_PHASES:
                raise ValueError(
                    f"Invalid phase name '{phase}'. Must be one of "
                    f"{sorted(list(self.VALID_PHASES))}."
                )

        self._green_time = green_time
        self._yellow_time = yellow_time
        self._all_red_time = all_red_time
        self._offset = offset

        # Timing states
        self._current_phase_index = 0
        self._phase_time_elapsed = 0.0
        self._cycle_number = 1

        # Apply start offset if positive
        if self._offset > 0:
            self.update(self._offset, [])

    @property
    def current_phase(self) -> str:
        """Get the current active phase name."""
        return self._phase_sequence[self._current_phase_index]

    @property
    def cycle_number(self) -> int:
        """Get the current cycle number."""
        return self._cycle_number

    def _get_phase_duration(self, phase_name: str) -> float:
        """Get the duration of a given phase.

        Args:
            phase_name: Name of the phase.

        Returns:
            Duration in seconds.
        """
        if phase_name in ("ns_green", "ew_green"):
            return self._green_time
        if phase_name in ("ns_yellow", "ew_yellow"):
            return self._yellow_time
        return self._all_red_time

    def update(self, delta_time: float, active_vehicles: List[Vehicle]) -> None:
        """Update the signal phase timings based on delta_time.

        Args:
            delta_time: Elapsed time in seconds.
            active_vehicles: List of active vehicles (unused).
        """
        if delta_time <= 0:
            return

        self._phase_time_elapsed += delta_time

        while True:
            duration = self._get_phase_duration(self.current_phase)
            if self._phase_time_elapsed >= duration:
                self._phase_time_elapsed -= duration
                self._current_phase_index = (self._current_phase_index + 1) % len(
                    self._phase_sequence
                )
                if self._current_phase_index == 0:
                    self._cycle_number += 1
            else:
                break

    def get_signals_state(self) -> List[Dict[str, str]]:
        """Get the current color state for all 4 direction signal heads.

        Returns:
            List of dictionaries representing SignalHead states.
        """
        phase = self.current_phase
        if phase == "ns_green":
            return [
                {"direction": "north", "color": "green"},
                {"direction": "south", "color": "green"},
                {"direction": "east", "color": "red"},
                {"direction": "west", "color": "red"},
            ]
        elif phase == "ns_yellow":
            return [
                {"direction": "north", "color": "yellow"},
                {"direction": "south", "color": "yellow"},
                {"direction": "east", "color": "red"},
                {"direction": "west", "color": "red"},
            ]
        elif phase == "ew_green":
            return [
                {"direction": "north", "color": "red"},
                {"direction": "south", "color": "red"},
                {"direction": "east", "color": "green"},
                {"direction": "west", "color": "green"},
            ]
        elif phase == "ew_yellow":
            return [
                {"direction": "north", "color": "red"},
                {"direction": "south", "color": "red"},
                {"direction": "east", "color": "yellow"},
                {"direction": "west", "color": "yellow"},
            ]
        else:  # all_red
            return [
                {"direction": "north", "color": "red"},
                {"direction": "south", "color": "red"},
                {"direction": "east", "color": "red"},
                {"direction": "west", "color": "red"},
            ]

    def get_state(self) -> Dict[str, Any]:
        """Get the snapshot state of the controller.

        Returns:
            ControllerState dictionary conforming to contract schema.
        """
        duration = self._get_phase_duration(self.current_phase)
        remaining = max(0.0, duration - self._phase_time_elapsed)

        return {
            "type": "fixed_time_signal",
            "timeInCurrentState": self._phase_time_elapsed,
            "currentPhase": self.current_phase,
            "phaseTimeRemaining": remaining,
            "cycleNumber": self._cycle_number,
            "signals": self.get_signals_state(),
        }

    def reset(self) -> None:
        """Reset the controller back to initial state, reapplying offset."""
        self._current_phase_index = 0
        self._phase_time_elapsed = 0.0
        self._cycle_number = 1
        if self._offset > 0:
            self.update(self._offset, [])
