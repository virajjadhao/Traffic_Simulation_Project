import pytest

from src.core.enums import Direction, TurnIntent, VehicleState
from src.metrics.collector import MetricCollector
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(
    vehicle_id: str, spawn_time: float, exit_time: float | None = None
) -> Vehicle:
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
    if exit_time is not None:
        v.exit_time = exit_time
        v.state = VehicleState.EXITED
    return v


def test_collector_init() -> None:
    """Verify that parameters are validated during initialization."""
    # Valid
    collector = MetricCollector(update_frequency=2.0, warmup_time=15.0)
    assert collector.update_frequency == 2.0
    assert collector.warmup_time == 15.0

    # Invalid frequency
    with pytest.raises(ValueError, match="update_frequency must be greater"):
        MetricCollector(update_frequency=0.0)

    # Invalid warmup
    with pytest.raises(ValueError, match="warmup_time cannot be negative"):
        MetricCollector(warmup_time=-5.0)


def test_collector_is_in_warmup() -> None:
    """Verify is_in_warmup method boundaries."""
    collector = MetricCollector(warmup_time=30.0)
    assert collector.is_in_warmup(0.0) is True
    assert collector.is_in_warmup(15.0) is True
    assert collector.is_in_warmup(29.99) is True
    assert collector.is_in_warmup(30.0) is False
    assert collector.is_in_warmup(45.0) is False


def test_collector_should_update() -> None:
    """Verify update interval ticking logic."""
    # 2 Hz = every 0.5s
    collector = MetricCollector(update_frequency=2.0)
    assert collector.should_update(0.1) is False
    assert collector.should_update(0.1) is False
    assert collector.should_update(0.3) is True  # Total 0.5s reached
    assert collector.should_update(0.4) is False
    assert collector.should_update(0.1) is True  # Total 0.5s reached again


def test_collector_get_valid_vehicles() -> None:
    """Verify vehicle warmup filtering logic."""
    collector = MetricCollector(warmup_time=30.0)

    # Spawned during warmup -> Invalid
    v1 = _make_mock_vehicle("v1", spawn_time=10.0)

    # Spawned post-warmup, still active -> Valid
    v2 = _make_mock_vehicle("v2", spawn_time=35.0)

    # Spawned post-warmup, exited during warmup
    # (impossible sequence, but checks logic) -> Invalid
    v3 = _make_mock_vehicle("v3", spawn_time=35.0, exit_time=20.0)

    # Spawned post-warmup, exited post-warmup -> Valid
    v4 = _make_mock_vehicle("v4", spawn_time=35.0, exit_time=45.0)

    # Missing spawn time (safety check) -> Invalid
    v5 = _make_mock_vehicle("v5", spawn_time=0.0)
    v5.spawn_time = None

    valid = collector.get_valid_vehicles([v1, v2, v3, v4, v5])
    assert len(valid) == 2
    assert v2 in valid
    assert v4 in valid


def test_collector_update_warmup() -> None:
    """Verify that update ignores ticks inside warmup and logs afterward."""
    # 1 Hz = every 1s
    collector = MetricCollector(update_frequency=1.0, warmup_time=10.0)

    v_active = [_make_mock_vehicle("v1", spawn_time=15.0)]

    # Tick at 5.0s (in warmup) -> Should be ignored
    collector.update(1.0, 5.0, v_active, [])
    assert len(collector.history) == 0

    # Tick at 11.0s (post-warmup) -> Should log to history
    collector.update(1.0, 11.0, v_active, [])
    assert len(collector.history) == 1
    assert collector.history[0]["time"] == 11.0
    assert collector.history[0]["active_count"] == 1


def test_collector_reset() -> None:
    """Verify reset functionality clears state."""
    collector = MetricCollector(update_frequency=1.0, warmup_time=10.0)
    v_active = [_make_mock_vehicle("v1", spawn_time=15.0)]

    collector.update(1.0, 11.0, v_active, [])
    assert len(collector.history) == 1

    collector.reset()
    assert len(collector.history) == 0
