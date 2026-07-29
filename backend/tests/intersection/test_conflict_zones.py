import pytest
from src.core.enums import Direction, TurnIntent
from src.roads.network import RoadNetwork
from src.intersection.conflict_zones import ConflictZoneDetector
from src.vehicles.vehicle import Vehicle


def _make_network() -> RoadNetwork:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    return net


def test_conflict_zone_detector_safety_buffer_validation() -> None:
    # Valid safety buffer
    ConflictZoneDetector(safety_buffer=1.5)
    
    # Invalid safety buffer
    with pytest.raises(ValueError, match="Safety buffer cannot be negative"):
        ConflictZoneDetector(safety_buffer=-0.1)


def test_no_conflict_same_lane() -> None:
    network = _make_network()
    route = network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )

    v1 = Vehicle("v1", length=4.0, width=2.0, desired_speed=10.0, route=route, start_position=50.0)
    v2 = Vehicle("v2", length=4.0, width=2.0, desired_speed=10.0, route=route, start_position=20.0)

    detector = ConflictZoneDetector()
    
    # Same lane vehicles are ignored by ConflictZoneDetector
    assert detector.check_conflicts(v1, [v1, v2]) == float("inf")
    assert detector.check_conflicts(v2, [v1, v2]) == float("inf")


def test_perpendicular_conflict() -> None:
    network = _make_network()
    route_ns = network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )
    route_we = network.generate_route(
        Direction.WEST, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )

    # v_ns is 10m from end of incoming lane (dist_to_P = 10m + 5.25m = 15.25m)
    v_ns = Vehicle("v_ns", length=4.0, width=2.0, desired_speed=10.0, route=route_ns, start_position=90.0)
    # v_we is 5m from end of incoming lane (dist_to_P = 5m + 1.75m = 6.75m)
    v_we = Vehicle("v_we", length=4.0, width=2.0, desired_speed=10.0, route=route_we, start_position=95.0)

    detector = ConflictZoneDetector(safety_buffer=2.0)
    
    # v_we is closer, so it has priority. v_ns must yield.
    # gap for v_ns = 11.75 - 2.0 (half length) - 2.0 (buffer) = 7.75m
    assert pytest.approx(detector.check_conflicts(v_ns, [v_ns, v_we])) == 7.75
    
    # v_we has priority, so it shouldn't yield
    assert detector.check_conflicts(v_we, [v_ns, v_we]) == float("inf")


def test_occupying_priority() -> None:
    network = _make_network()
    route_ns = network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )
    route_we = network.generate_route(
        Direction.WEST, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )

    # v_we is inside the intersection, crossing the conflict point P (-1.75, -1.75)
    # P is 1.75m along connection lane. v_we position = 1.75m (on connection lane)
    # So v_we is on lane index 1, position 1.75m. dist_other = 0.0 (center exactly on P)
    # v_we length = 4.0, so it occupies [-2.0, 2.0]. It is occupying P.
    v_we = Vehicle("v_we", length=4.0, width=2.0, desired_speed=10.0, route=route_we, start_position=96.5)
    # Move it to connection lane
    v_we.update_state(0.0, 1.0) # moves it past 100m, now on connection lane
    
    # v_ns is approaching, 15m from end of incoming lane
    v_ns = Vehicle("v_ns", length=4.0, width=2.0, desired_speed=10.0, route=route_ns, start_position=85.0)

    detector = ConflictZoneDetector(safety_buffer=1.0)
    
    # v_we occupies P, so v_we has priority. v_ns must yield.
    # dist_subj = 11.5m + 5.25m = 16.75m
    # gap for v_ns = 16.75 - 2.0 - 1.0 = 13.75m
    assert pytest.approx(detector.check_conflicts(v_ns, [v_ns, v_we])) == 13.75
    assert detector.check_conflicts(v_we, [v_ns, v_we]) == float("inf")
