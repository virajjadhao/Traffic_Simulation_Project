from typing import Tuple

import pytest

from src.controllers.roundabout import RoundaboutController
from src.core.enums import Direction, VehicleState


class MockVehicle:
    """Mock vehicle class for controller unit tests."""

    def __init__(
        self,
        current_lane_index: int,
        state: VehicleState,
        coords: Tuple[float, float],
        speed: float,
    ) -> None:
        self.current_lane_index = current_lane_index
        self.state = state
        self.coords = coords
        self.speed = speed


def test_roundabout_initialization() -> None:
    ctrl = RoundaboutController()
    state = ctrl.get_state()
    assert state["type"] == "roundabout"
    assert state["timeInCurrentState"] == 0.0
    assert state["innerRadius"] == 10.0
    assert state["outerRadius"] == 20.0
    assert state["circulatingCount"] == 0

    # Initially all entries are clear
    assert ctrl.yield_signals[Direction.NORTH] is True
    assert ctrl.yield_signals[Direction.SOUTH] is True
    assert ctrl.yield_signals[Direction.EAST] is True
    assert ctrl.yield_signals[Direction.WEST] is True


def test_roundabout_validation() -> None:
    # Invalid inner_radius
    with pytest.raises(ValueError, match="inner_radius must be in"):
        RoundaboutController(inner_radius=4.0)

    # Invalid outer_radius
    with pytest.raises(ValueError, match="outer_radius must be greater"):
        RoundaboutController(inner_radius=15.0, outer_radius=12.0)

    # Invalid circulating_lanes
    with pytest.raises(ValueError, match="circulating_lanes must be in"):
        RoundaboutController(circulating_lanes=0)

    # Invalid critical_gap
    with pytest.raises(ValueError, match="critical_gap must be in"):
        RoundaboutController(critical_gap=-0.1)

    # Invalid follow_up_time
    with pytest.raises(ValueError, match="follow_up_time must be positive"):
        RoundaboutController(follow_up_time=0.0)

    # Invalid entry_speed
    with pytest.raises(ValueError, match="entry_speed must be positive"):
        RoundaboutController(entry_speed=-1.0)


def test_roundabout_yield_logic() -> None:
    # R_inner=10, R_outer=20. Avg R = 15.0.
    ctrl = RoundaboutController(inner_radius=10.0, outer_radius=20.0, critical_gap=4.0)

    # 1. No circulating vehicles
    ctrl.update(0.1, [])
    assert ctrl.yield_signals[Direction.NORTH] is True
    assert ctrl.yield_signals[Direction.SOUTH] is True

    # 2. Add vehicle in North conflict zone: Direction.NORTH entry angle is pi/2
    # Conflict zone: [0, pi/2]. Let's place vehicle at theta = pi/4
    # (x=10.6, y=10.6, R=15.0)
    # delta_theta = pi/2 - pi/4 = pi/4 ~ 0.785
    # dist = 0.785 * 15.0 = 11.78 meters
    v_circ = MockVehicle(
        current_lane_index=1,
        state=VehicleState.IN_ROUNDABOUT,
        coords=(10.606, 10.606),
        speed=2.0,
    )
    # gap_time = 11.78 / 2.0 = 5.89 seconds.
    # critical_gap is 4.0, so 5.89 >= 4.0 -> Should be safe
    ctrl.update(0.1, [v_circ])  # type: ignore[list-item]
    assert ctrl.yield_signals[Direction.NORTH] is True
    assert ctrl.get_state()["circulatingCount"] == 1

    # Increase critical_gap to 6.0. Now 5.89 < 6.0 -> Should NOT be safe (yield)
    ctrl_unsafe = RoundaboutController(critical_gap=6.0)
    ctrl_unsafe.update(0.1, [v_circ])  # type: ignore[list-item]
    assert ctrl_unsafe.yield_signals[Direction.NORTH] is False

    # 3. Add slow/stopped vehicle inside yield zone
    v_stopped = MockVehicle(
        current_lane_index=1,
        state=VehicleState.IN_ROUNDABOUT,
        coords=(10.606, 10.606),
        speed=0.1,
    )
    # dist = 11.78 < 15.0 -> Should yield
    ctrl.update(0.1, [v_stopped])  # type: ignore[list-item]
    assert ctrl.yield_signals[Direction.NORTH] is False


def test_roundabout_reset() -> None:
    ctrl = RoundaboutController()
    ctrl.update(10.0, [])
    assert ctrl.get_state()["timeInCurrentState"] == 10.0

    ctrl.reset()
    assert ctrl.get_state()["timeInCurrentState"] == 0.0
    assert ctrl.get_state()["circulatingCount"] == 0
