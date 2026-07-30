from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.definitions.wait_time import calculate_average_wait_time
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, wait_time: float) -> Vehicle:
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
    # Force set wait time
    v._cumulative_wait_time = wait_time
    return v


def test_calculate_average_wait_time_empty() -> None:
    """Verify that average wait time handles empty exited vehicle list."""
    res = calculate_average_wait_time([])
    assert res["value"] == 0.0
    assert res["unit"] == "seconds"
    assert res["sampleSize"] == 0
    assert res["confidence"] == "low"


def test_calculate_average_wait_time_values() -> None:
    """Verify math for average wait time calculation."""
    v1 = _make_mock_vehicle("v1", 10.0)
    v2 = _make_mock_vehicle("v2", 20.0)
    v3 = _make_mock_vehicle("v3", 15.0)

    res = calculate_average_wait_time([v1, v2, v3])
    # Average should be (10 + 20 + 15) / 3 = 15.0
    assert res["value"] == 15.0
    assert res["sampleSize"] == 3
    assert res["confidence"] == "low"  # sample size 3 < 10


def test_calculate_average_wait_time_confidence() -> None:
    """Verify confidence ratings based on sample size thresholds."""
    # Create 10 vehicles
    vehicles = [_make_mock_vehicle(f"v{i}", 12.0) for i in range(10)]

    res = calculate_average_wait_time(vehicles)
    assert res["value"] == 12.0
    assert res["sampleSize"] == 10
    assert res["confidence"] == "high"  # sample size 10 >= 10
