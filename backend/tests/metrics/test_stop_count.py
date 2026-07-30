import pytest

from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.definitions.stop_count import calculate_stop_count
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, stop_count: int) -> Vehicle:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    route = net.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    v = Vehicle(
        vehicle_id=vehicle_id,
        length=4.0,
        width=2.0,
        desired_speed=15.0,
        route=route,
        start_position=0.0,
    )
    v.spawn_time = 0.0
    v.exit_time = 50.0
    v.state = VehicleState.EXITED
    # Force set stop count
    v._stop_count = stop_count
    return v


def test_calculate_stop_count_empty() -> None:
    """Verify stop count statistics with empty exited vehicle list."""
    res = calculate_stop_count([])
    assert res["value"] == 0.0
    assert res["unit"] == "stops_per_vehicle"
    assert res["total"] == 0


def test_calculate_stop_count_values() -> None:
    """Verify average stop count and total stops math."""
    v1 = _make_mock_vehicle("v1", 2)
    v2 = _make_mock_vehicle("v2", 3)
    v3 = _make_mock_vehicle("v3", 1)

    res = calculate_stop_count([v1, v2, v3])
    # Total = 6, Avg = 2.0
    assert res["value"] == 2.0
    assert res["total"] == 6
    assert res["unit"] == "stops_per_vehicle"


def test_vehicle_speed_hysteresis() -> None:
    """Verify that speed oscillations near stop threshold do not double-count stops."""
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    route = net.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    v = Vehicle(
        vehicle_id="veh",
        length=4.0,
        width=2.0,
        desired_speed=15.0,
        route=route,
        start_position=0.0,
        initial_speed=5.0,
    )

    # Initial state: moving at 5.0 m/s
    assert v.stop_count == 0

    # Speed drops below stopSpeedThreshold (0.1 m/s) -> 1 stop counted
    v.update_state(acceleration=-49.5, dt=0.1)  # speed becomes 0.05 m/s
    assert pytest.approx(v.speed) == 0.05
    assert v.stop_count == 1

    # Speed oscillates slightly to 0.15 m/s (above 0.1 but below 0.2 hysteresis limit)
    # This should NOT clear the stopped state, so stop count remains 1
    v._speed = 0.15
    v.update_state(acceleration=0.0, dt=0.1)
    assert v.stop_count == 1

    # Speed drops back below 0.1 m/s -> still 1 stop because stopped state
    # was never cleared
    v._speed = 0.05
    v.update_state(acceleration=0.0, dt=0.1)
    assert v.stop_count == 1

    # Speed increases to 0.25 m/s (above 2 * 0.1 = 0.2 m/s hysteresis limit)
    # Stopped state should clear
    v._speed = 0.25
    v.update_state(acceleration=0.0, dt=0.1)
    assert v.stop_count == 1

    # Speed drops below 0.1 m/s again -> 2nd stop counted
    v._speed = 0.05
    v.update_state(acceleration=0.0, dt=0.1)
    assert v.stop_count == 2
