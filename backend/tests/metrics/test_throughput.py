import pytest

from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.definitions.throughput import calculate_throughput
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, exit_time: float) -> Vehicle:
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
    v.exit_time = exit_time
    v.state = VehicleState.EXITED
    return v


def test_calculate_throughput_empty() -> None:
    """Verify throughput with empty exited vehicle list."""
    res = calculate_throughput([], elapsed_time=10.0, warmup_time=10.0)
    assert res["value"] == 0
    assert res["rate"] == 0.0
    assert res["unit"] == "vehicles"
    assert res["rateUnit"] == "vehicles_per_minute"


def test_calculate_throughput_partial_window() -> None:
    """Verify rolling rate calculation during the initial partial window."""
    # Warmup ends at 30.0s. Current time is 45.0s (15s elapsed post-warmup).
    # 2 vehicles exited post-warmup (at 35s and 40s).
    v1 = _make_mock_vehicle("v1", exit_time=35.0)
    v2 = _make_mock_vehicle("v2", exit_time=40.0)

    res = calculate_throughput(
        [v1, v2], elapsed_time=45.0, warmup_time=30.0, window_size=60.0
    )
    # Total count = 2
    assert res["value"] == 2
    # dt_window = 45.0 - 30.0 = 15.0s
    # rate = (2 / 15.0) * 60 = 8.0 vehicles/minute
    assert pytest.approx(res["rate"]) == 8.0


def test_calculate_throughput_full_window() -> None:
    """Verify rolling rate calculation with a full window size, ignoring old events."""
    # Warmup ends at 30.0s. Current time is 100.0s.
    # Window size = 60s -> window is from 40.0s to 100.0s.
    # Exits:
    # - v1 at 35.0s (inside warmup? No, warmup ends at 30s,
    #   so it is valid, but outside window [40, 100])
    # - v2 at 45.0s (inside window)
    # - v3 at 60.0s (inside window)
    # - v4 at 95.0s (inside window)
    v1 = _make_mock_vehicle("v1", exit_time=35.0)
    v2 = _make_mock_vehicle("v2", exit_time=45.0)
    v3 = _make_mock_vehicle("v3", exit_time=60.0)
    v4 = _make_mock_vehicle("v4", exit_time=95.0)

    res = calculate_throughput(
        [v1, v2, v3, v4], elapsed_time=100.0, warmup_time=30.0, window_size=60.0
    )
    # Total count = 4
    assert res["value"] == 4
    # dt_window = 60.0s (100 - 40)
    # Vehicles in window [40, 100] = 3 (v2, v3, v4)
    # rate = (3 / 60.0) * 60 = 3.0 vehicles/minute
    assert pytest.approx(res["rate"]) == 3.0
