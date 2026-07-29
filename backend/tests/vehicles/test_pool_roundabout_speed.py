import math

from src.controllers.roundabout import RoundaboutController
from src.core.enums import Direction, TurnIntent, VehicleState
from src.roads.network import RoadNetwork
from src.vehicles.idm import IntelligentDriverModel
from src.vehicles.pool import VehiclePool
from src.vehicles.spawner import VehicleSpawner
from src.vehicles.vehicle import Vehicle


def _make_network() -> RoadNetwork:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=15.0,
        lanes_per_approach=1,
    )
    return net


def test_roundabout_circulating_speed_and_splines() -> None:
    """Verify trajectory overrides and speed limit overrides in roundabout."""
    network = _make_network()
    spawner = VehicleSpawner(network, arrival_rate=1.0, total_vehicles=1)
    spawner.try_spawn = lambda t: None  # type: ignore[assignment]
    idm = IntelligentDriverModel()

    # Controller with target speed 8.0 m/s
    ctrl = RoundaboutController(circulating_speed=8.0)
    pool = VehiclePool(spawner, idm)

    # Spawn vehicle from North with desired speed 15.0 m/s
    route = network.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    v = Vehicle(
        "v1",
        length=4.0,
        width=2.0,
        desired_speed=15.0,
        route=route,
        start_position=80.0,
        initial_speed=10.0,
    )
    pool._active.append(v)

    # 1. Incoming lane: No overrides, normal desired speed
    ctrl.update(0.1, pool.active_vehicles)
    assert v.state == VehicleState.APPROACHING
    assert v.coords_override is None
    assert v.heading_override is None
    assert v.speed_limit_override is None
    assert v.desired_speed == 15.0

    # 2. Connection lane: overrides applied, state is IN_ROUNDABOUT
    # Move it past 96.5m (incoming length) to connection lane
    v.update_state(acceleration=0.0, dt=2.0)
    assert v.current_lane_index == 1

    ctrl.update(0.1, pool.active_vehicles)
    assert v.state == VehicleState.IN_ROUNDABOUT
    assert v.speed_limit_override == 8.0
    assert v.desired_speed == 8.0

    # Coords override should be set
    assert v.coords_override is not None
    # Verify coordinates trace a circle: distance from center (0, 0) should be
    # between inner_radius (10) and outer_radius (20)
    dist_from_center = math.sqrt(v.coords[0] ** 2 + v.coords[1] ** 2)
    assert 10.0 <= dist_from_center <= 20.0

    # Heading override should be set
    assert v.heading_override is not None

    # 3. Exit lane: overrides cleared, state restored to APPROACHING
    # Move it past connection lane length (which is ~7.0m) to exit lane
    # We move it by 20.0m to guarantee it enters exit lane (index 2)
    v.update_state(acceleration=0.0, dt=5.0)
    assert v.current_lane_index == 2

    ctrl.update(0.1, pool.active_vehicles)
    assert v.state == VehicleState.APPROACHING
    assert v.coords_override is None
    assert v.heading_override is None
    assert v.speed_limit_override is None
    assert v.desired_speed == 15.0
