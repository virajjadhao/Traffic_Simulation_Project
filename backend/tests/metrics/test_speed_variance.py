import pytest

from src.core.enums import Direction, TurnIntent
from src.metrics.definitions.speed_variance import (
    calculate_active_cv,
    calculate_speed_variance_index,
)
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, speed: float) -> Vehicle:
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
    v._speed = speed
    return v


def test_calculate_active_cv_insufficient_sample() -> None:
    """Verify active CV returns None when fewer than 2 active vehicles are present."""
    v1 = _make_mock_vehicle("v1", 10.0)
    assert calculate_active_cv([]) is None
    assert calculate_active_cv([v1]) is None


def test_calculate_active_cv_zero_speed() -> None:
    """Verify active CV returns 0.0 when mean speed is zero."""
    v1 = _make_mock_vehicle("v1", 0.0)
    v2 = _make_mock_vehicle("v2", 0.0)
    assert calculate_active_cv([v1, v2]) == 0.0


def test_calculate_active_cv_calculation() -> None:
    """Verify math for active speed CV calculation."""
    # Speeds: [6.0, 12.0]
    # Mean: (6 + 12) / 2 = 9.0
    # Variance: ((6-9)^2 + (12-9)^2) / 2 = (9 + 9) / 2 = 9.0
    # SD: sqrt(9.0) = 3.0
    # CV: 3.0 / 9.0 = 1/3 = 0.3333333333333333
    v1 = _make_mock_vehicle("v1", 6.0)
    v2 = _make_mock_vehicle("v2", 12.0)
    cv = calculate_active_cv([v1, v2])
    assert cv is not None
    assert pytest.approx(cv) == 1.0 / 3.0


def test_calculate_speed_variance_index() -> None:
    """Verify SVI calculates correct averages over history."""
    # Empty history
    res = calculate_speed_variance_index([])
    assert res["value"] == 0.0
    assert res["unit"] == "dimensionless"

    # With values
    res = calculate_speed_variance_index([0.2, 0.4, None, 0.6])
    # Average should ignore None: (0.2 + 0.4 + 0.6) / 3 = 0.4
    assert pytest.approx(res["value"]) == 0.4
