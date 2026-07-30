import pytest

from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.definitions.fairness import (
    calculate_directional_fairness,
    get_vehicle_origin_direction,
)
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(
    vehicle_id: str, direction: Direction, wait_time: float
) -> Vehicle:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    route = net.generate_route(direction, 0, TurnIntent.STRAIGHT)
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
    v._cumulative_wait_time = wait_time
    return v


def test_get_vehicle_origin_direction() -> None:
    """Verify helper extracts origin direction correctly from lane id."""
    v1 = _make_mock_vehicle("v1", Direction.NORTH, 10.0)
    v2 = _make_mock_vehicle("v2", Direction.SOUTH, 15.0)

    assert get_vehicle_origin_direction(v1) == "north"
    assert get_vehicle_origin_direction(v2) == "south"


def test_calculate_directional_fairness_empty() -> None:
    """Verify fairness calculation handles empty list."""
    res = calculate_directional_fairness([])
    assert res["value"] == 1.0
    assert res["unit"] == "dimensionless"
    assert res["perDirection"]["north"] == 0.0


def test_calculate_directional_fairness_uniform() -> None:
    """Verify fairness is 1.0 when all wait times are identical (fully fair)."""
    # 4 vehicles, 1 from each direction, all waited exactly 10s
    v1 = _make_mock_vehicle("v1", Direction.NORTH, 10.0)
    v2 = _make_mock_vehicle("v2", Direction.SOUTH, 10.0)
    v3 = _make_mock_vehicle("v3", Direction.EAST, 10.0)
    v4 = _make_mock_vehicle("v4", Direction.WEST, 10.0)

    res = calculate_directional_fairness([v1, v2, v3, v4])
    assert res["value"] == 1.0
    assert res["perDirection"]["north"] == 10.0
    assert res["perDirection"]["south"] == 10.0
    assert res["perDirection"]["east"] == 10.0
    assert res["perDirection"]["west"] == 10.0


def test_calculate_directional_fairness_asymmetric() -> None:
    """Verify index drops below 1.0 under asymmetric demand."""
    # 2 directions present: North (avg wait = 10s), South (avg wait = 20s)
    # n = 2.
    # Jain's index: (10 + 20)^2 / (2 * (100 + 400)) = 900 / 1000 = 0.9
    v1 = _make_mock_vehicle("v1", Direction.NORTH, 10.0)
    v2 = _make_mock_vehicle("v2", Direction.SOUTH, 20.0)

    res = calculate_directional_fairness([v1, v2])
    assert pytest.approx(res["value"]) == 0.9
    assert res["perDirection"]["north"] == 10.0
    assert res["perDirection"]["south"] == 20.0
    assert res["perDirection"]["east"] == 0.0
    assert res["perDirection"]["west"] == 0.0
