import pytest
from src.controllers.fixed_time_signal import FixedTimeSignalController


def test_fixed_time_signal_initialization() -> None:
    # Default values
    ctrl = FixedTimeSignalController()
    assert ctrl.current_phase == "ns_green"
    assert ctrl.cycle_number == 1
    
    state = ctrl.get_state()
    assert state["type"] == "fixed_time_signal"
    assert state["timeInCurrentState"] == 0.0
    assert state["phaseTimeRemaining"] == 30.0
    assert state["cycleNumber"] == 1
    assert len(state["signals"]) == 4


def test_fixed_time_signal_validation() -> None:
    # Invalid green_time
    with pytest.raises(ValueError, match="Green and yellow phase times must be positive"):
        FixedTimeSignalController(green_time=0.0)
    
    # Invalid yellow_time
    with pytest.raises(ValueError, match="Green and yellow phase times must be positive"):
        FixedTimeSignalController(yellow_time=-1.0)
        
    # Invalid all_red_time
    with pytest.raises(ValueError, match="All-red phase time cannot be negative"):
        FixedTimeSignalController(all_red_time=-0.1)

    # Invalid offset
    with pytest.raises(ValueError, match="Offset cannot be negative"):
        FixedTimeSignalController(offset=-5.0)

    # Empty phase sequence
    with pytest.raises(ValueError, match="Phase sequence cannot be empty"):
        FixedTimeSignalController(phase_sequence=[])

    # Invalid phase name
    with pytest.raises(ValueError, match="Invalid phase name 'invalid_phase'"):
        FixedTimeSignalController(phase_sequence=["ns_green", "invalid_phase"])


def test_phase_transitions() -> None:
    # green=10s, yellow=2s, all_red=1s
    ctrl = FixedTimeSignalController(green_time=10.0, yellow_time=2.0, all_red_time=1.0)
    
    # Init: ns_green
    assert ctrl.current_phase == "ns_green"
    assert ctrl.get_state()["phaseTimeRemaining"] == 10.0
    
    # Advance near transition
    ctrl.update(9.9, [])
    assert ctrl.current_phase == "ns_green"
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 0.1
    
    # Tick past transition: ns_green -> ns_yellow
    ctrl.update(0.1, [])
    assert ctrl.current_phase == "ns_yellow"
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 2.0
    
    # Tick past yellow: ns_yellow -> all_red
    ctrl.update(2.0, [])
    assert ctrl.current_phase == "all_red"
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 1.0
    
    # Tick past all_red: all_red -> ew_green
    ctrl.update(1.0, [])
    assert ctrl.current_phase == "ew_green"
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 10.0


def test_carryover_timing_overflow() -> None:
    # green=10s, yellow=2s, all_red=1s
    # Total cycle duration = 10 + 2 + 1 + 10 + 2 + 1 = 26s
    ctrl = FixedTimeSignalController(green_time=10.0, yellow_time=2.0, all_red_time=1.0)
    
    # Update by a single large time step (14.0s)
    # ns_green (10s) -> ns_yellow (2s) -> all_red (1s) -> ew_green (remaining 1.0s elapsed)
    ctrl.update(14.0, [])
    assert ctrl.current_phase == "ew_green"
    assert pytest.approx(ctrl.get_state()["timeInCurrentState"]) == 1.0
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 9.0
    assert ctrl.cycle_number == 1

    # Large update spanning across cycles (e.g. additional 40.0s)
    # Spans remainder of ew_green (9.0s), ew_yellow (2.0s), all_red (1.0s), which completes cycle 1 (12.0s)
    # Starts cycle 2: ns_green (10.0s), ns_yellow (2.0s), all_red (1.0s), ew_green (10.0s), ew_yellow (2.0s), all_red (1.0s)
    # 40.0s - 12.0s = 28.0s (completed cycle 1, now in cycle 2)
    # 28.0s - 26.0s (full cycle 2 duration) = 2.0s (starts cycle 3)
    # In cycle 3: ns_green (2.0s elapsed)
    ctrl.update(40.0, [])
    assert ctrl.current_phase == "ns_green"
    assert pytest.approx(ctrl.get_state()["timeInCurrentState"]) == 2.0
    assert pytest.approx(ctrl.get_state()["phaseTimeRemaining"]) == 8.0
    assert ctrl.cycle_number == 3


def test_offset_at_start() -> None:
    # green=10s, yellow=2s, all_red=1s
    # Starts with 14.0s offset
    ctrl = FixedTimeSignalController(
        green_time=10.0, yellow_time=2.0, all_red_time=1.0, offset=14.0
    )
    
    # Should start immediately in ew_green with 1.0s elapsed
    assert ctrl.current_phase == "ew_green"
    assert pytest.approx(ctrl.get_state()["timeInCurrentState"]) == 1.0
    assert ctrl.cycle_number == 1
    
    # Reset should preserve the offset
    ctrl.reset()
    assert ctrl.current_phase == "ew_green"
    assert pytest.approx(ctrl.get_state()["timeInCurrentState"]) == 1.0
    assert ctrl.cycle_number == 1


def test_signal_head_colors() -> None:
    ctrl = FixedTimeSignalController(green_time=10.0, yellow_time=2.0, all_red_time=1.0)
    
    # ns_green colors
    signals = ctrl.get_signals_state()
    colors = {sig["direction"]: sig["color"] for sig in signals}
    assert colors["north"] == "green"
    assert colors["south"] == "green"
    assert colors["east"] == "red"
    assert colors["west"] == "red"
    
    # ns_yellow colors
    ctrl.update(10.0, [])
    signals = ctrl.get_signals_state()
    colors = {sig["direction"]: sig["color"] for sig in signals}
    assert colors["north"] == "yellow"
    assert colors["south"] == "yellow"
    
    # ew_green colors
    ctrl.update(3.0, []) # moves yellow(2s) + all_red(1s)
    signals = ctrl.get_signals_state()
    colors = {sig["direction"]: sig["color"] for sig in signals}
    assert colors["north"] == "red"
    assert colors["south"] == "red"
    assert colors["east"] == "green"
    assert colors["west"] == "green"
