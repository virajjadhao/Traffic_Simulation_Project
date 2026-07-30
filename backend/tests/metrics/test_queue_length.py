from src.core.enums import Direction, TurnIntent
from src.metrics.definitions.queue_length import QueueLengthTracker
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle


def _make_mock_vehicle(vehicle_id: str, direction: Direction, speed: float) -> Vehicle:
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
    v._speed = speed
    return v


def test_queue_length_tracker_init_and_reset() -> None:
    """Verify tracker initialization and reset functionality."""
    tracker = QueueLengthTracker(wait_speed_threshold=0.8)
    assert tracker.wait_speed_threshold == 0.8
    assert len(tracker._history["north"]) == 0

    tracker._history["north"].append(5)
    tracker.reset()
    assert len(tracker._history["north"]) == 0


def test_queue_length_tracker_record_tick() -> None:
    """Verify record_tick counts queued vehicles correctly per direction."""
    tracker = QueueLengthTracker(wait_speed_threshold=0.5)

    # Setup a mock road network
    network = RoadNetwork()
    network.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )

    # Add vehicles directly to network approach lanes
    v1 = _make_mock_vehicle("v1", Direction.NORTH, speed=0.1)  # Queued
    v2 = _make_mock_vehicle("v2", Direction.NORTH, speed=0.8)  # Not queued
    v3 = _make_mock_vehicle("v3", Direction.SOUTH, speed=0.3)  # Queued
    v4 = _make_mock_vehicle("v4", Direction.EAST, speed=0.4)  # Queued
    v5 = _make_mock_vehicle("v5", Direction.EAST, speed=0.2)  # Queued

    # Manually register vehicles on approach lanes
    network.get_incoming_approach(Direction.NORTH).get_lanes()[0].add_vehicle(v1)
    network.get_incoming_approach(Direction.NORTH).get_lanes()[0].add_vehicle(v2)
    network.get_incoming_approach(Direction.SOUTH).get_lanes()[0].add_vehicle(v3)
    network.get_incoming_approach(Direction.EAST).get_lanes()[0].add_vehicle(v4)
    network.get_incoming_approach(Direction.EAST).get_lanes()[0].add_vehicle(v5)

    current = tracker.record_tick(network)

    assert current["north"] == 1
    assert current["south"] == 1
    assert current["east"] == 2
    assert current["west"] == 0

    assert tracker._history["north"] == [1]
    assert tracker._history["south"] == [1]
    assert tracker._history["east"] == [2]
    assert tracker._history["west"] == [0]


def test_queue_length_tracker_statistics() -> None:
    """Verify statistics calculations match mathematical expectations."""
    tracker = QueueLengthTracker(wait_speed_threshold=0.5)

    # Manually populate history to test statistical formulas:
    # North: [1, 2, 3] -> Avg: 2.0, Max: 3
    # South: [0, 1, 2] -> Avg: 1.0, Max: 2
    # East:  [2, 4, 6] -> Avg: 4.0, Max: 6
    # West:  [0, 0, 0] -> Avg: 0.0, Max: 0
    tracker._history["north"] = [1, 2, 3]
    tracker._history["south"] = [0, 1, 2]
    tracker._history["east"] = [2, 4, 6]
    tracker._history["west"] = [0, 0, 0]

    stats = tracker.calculate_statistics()

    assert stats["unit"] == "vehicles"

    # Per direction assertions
    assert stats["perDirection"]["north"]["average"] == 2.0
    assert stats["perDirection"]["north"]["maximum"] == 3
    assert stats["perDirection"]["south"]["average"] == 1.0
    assert stats["perDirection"]["south"]["maximum"] == 2
    assert stats["perDirection"]["east"]["average"] == 4.0
    assert stats["perDirection"]["east"]["maximum"] == 6
    assert stats["perDirection"]["west"]["average"] == 0.0
    assert stats["perDirection"]["west"]["maximum"] == 0

    # Global average: mean of (2.0, 1.0, 4.0, 0.0) = 7.0 / 4 = 1.75
    assert stats["average"] == 1.75

    # Global maximum: max of all samples = 6
    assert stats["maximum"] == 6

    # 95th Percentile:
    # All samples sorted: [0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 4, 6] (len = 12)
    # 95th percentile index: int(12 * 0.95) = int(11.4) = 11
    # 11th index element (last element) is 6
    assert stats["percentile95"] == 6
