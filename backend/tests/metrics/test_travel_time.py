import pytest

from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.definitions.travel_time import calculate_travel_time_reliability
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, spawn_time: float, exit_time: float) -> Vehicle:
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
    v.spawn_time = spawn_time
    v.exit_time = exit_time
    v.state = VehicleState.EXITED
    return v


def test_calculate_travel_time_reliability_empty() -> None:
    """Verify PTI reliability outputs with empty exited vehicle list."""
    res = calculate_travel_time_reliability([])
    assert res["value"] == 1.0
    assert res["unit"] == "dimensionless"
    assert res["median_travel_time"] == 0.0
    assert res["p95_travel_time"] == 0.0


def test_calculate_travel_time_reliability_zero_median() -> None:
    """Verify PTI handles zero median travel time data error."""
    # Create vehicle with travel time = 0.0s (exit_time == spawn_time)
    v = _make_mock_vehicle("v1", spawn_time=10.0, exit_time=10.0)

    res = calculate_travel_time_reliability([v])
    assert res["value"] is None
    assert res["median_travel_time"] == 0.0
    assert res["p95_travel_time"] == 0.0


def test_calculate_travel_time_reliability_uniform() -> None:
    """Verify PTI is 1.0 when all travel times are identical (variance is zero)."""
    v1 = _make_mock_vehicle("v1", spawn_time=0.0, exit_time=25.0)
    v2 = _make_mock_vehicle("v2", spawn_time=10.0, exit_time=35.0)

    res = calculate_travel_time_reliability([v1, v2])
    # Both travel times are 25.0s
    assert res["value"] == 1.0
    assert res["median_travel_time"] == 25.0
    assert res["p95_travel_time"] == 25.0


def test_calculate_travel_time_reliability_math() -> None:
    """Verify median, 95th percentile, and ratio math logic."""
    # Let's mock a set of 20 travel times:
    # [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    # Length = 20.
    # Sorted is same.
    # Median: average of index 9 (19) and index 10 (20) = 19.5
    # 95th percentile index: int(20 * 0.95) = 19 -> element at idx 19 is 29
    # PTI = 29 / 19.5 = 1.487179...
    vehicles = [
        _make_mock_vehicle(f"v{i}", spawn_time=0.0, exit_time=float(10 + i))
        for i in range(20)
    ]

    res = calculate_travel_time_reliability(vehicles)
    assert res["median_travel_time"] == 19.5
    assert res["p95_travel_time"] == 29.0
    assert pytest.approx(res["value"]) == 29.0 / 19.5
