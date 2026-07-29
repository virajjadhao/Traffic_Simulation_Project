import pytest

from src.core.enums import Direction, TurnIntent
from src.roads.network import RoadNetwork
from src.vehicles.router import VirtualVehicle, find_leader
from src.vehicles.vehicle import Vehicle


@pytest.fixture
def sample_network() -> RoadNetwork:
    network = RoadNetwork()
    network.setup_default_intersection(
        approach_length=100.0, lane_width=3.5, lanes_per_approach=1
    )
    return network


def test_find_leader_same_lane(sample_network: RoadNetwork) -> None:
    route = sample_network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )

    # Leader vehicle at position 60
    v_lead = Vehicle(
        "lead",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route,
        start_position=60.0,
    )
    # Follower vehicle at position 20
    v_follow = Vehicle(
        "follow",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route,
        start_position=20.0,
    )

    leader, gap = find_leader(v_follow)
    assert leader == v_lead
    # (60 - 2) - (20 + 2) = 58 - 22 = 36 meters
    assert gap == 36.0


def test_find_leader_red_light(sample_network: RoadNetwork) -> None:
    route = sample_network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )
    v_follow = Vehicle(
        "follow",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route,
        start_position=80.0,
    )

    # Signal is green -> no virtual stop line leader
    signals = {Direction.NORTH: True}
    leader, gap = find_leader(v_follow, traffic_signals=signals)
    assert leader is None
    assert gap == float("inf")

    # Signal is red -> stop line virtual leader
    signals = {Direction.NORTH: False}
    leader, gap = find_leader(v_follow, traffic_signals=signals)
    assert isinstance(leader, VirtualVehicle)
    assert leader.vehicle_id == "stop_line_north"
    # Lane length: 96.5 (from 100 - 3.5). Pos: 80. Front: 82.
    # Gap: 96.5 - 82 = 14.5 meters
    assert pytest.approx(gap) == 14.5


def test_find_leader_cross_lane(sample_network: RoadNetwork) -> None:
    route = sample_network.generate_route(
        Direction.NORTH, lane_index=0, turn_intent=TurnIntent.STRAIGHT
    )
    # Incoming lane length: 96.5. Conn lane: 7.0. Exit lane: 96.5

    # Follower on incoming lane (pos 80, length 4)
    v_follow = Vehicle(
        "follow",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route,
        start_position=80.0,
    )
    # Leader already transitioned to connection lane (pos 90, length 4, speed 20)
    v_lead = Vehicle(
        "lead",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route,
        start_position=90.0,
        initial_speed=20.0,
    )
    # Force update state to advance it to connection lane
    v_lead.update_state(acceleration=0.0, dt=0.5)

    assert v_lead.current_lane_index == 1  # connection lane

    leader, gap = find_leader(v_follow)
    assert leader == v_lead
    # Spacing check:
    # Remaining on incoming: 96.5 - (80 + 2.0) = 14.5 meters.
    # Position on connection lane: v_lead.position - v_lead.length/2.0
    expected_gap = (96.5 - 82.0) + (v_lead.position - 2.0)
    assert pytest.approx(gap) == expected_gap
