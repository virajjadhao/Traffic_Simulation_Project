from typing import Any

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
        lane_width=3.5,
        lanes_per_approach=1,
    )
    return net


def test_pool_roundabout_yield_integration() -> None:
    """Verify that vehicles yield at the roundabout entry when conflict exists."""
    network = _make_network()
    # Spawner that doesn't spawn automatically
    spawner = VehicleSpawner(network, arrival_rate=1.0, total_vehicles=1)
    spawner.try_spawn = lambda t: None  # type: ignore[assignment]
    idm = IntelligentDriverModel(max_acceleration=2.0, comfort_deceleration=3.0)

    # Initialize roundabout controller with critical gap 6.0s
    ctrl = RoundaboutController(critical_gap=6.0)
    pool = VehiclePool(spawner, idm)

    # 1. Spawn entering vehicle on North approach (incoming length is 96.5m)
    route_north = network.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    v_enter = Vehicle(
        "v_enter",
        length=4.0,
        width=2.0,
        desired_speed=13.89,
        route=route_north,
        start_position=80.0,
        initial_speed=10.0,
    )
    pool._active.append(v_enter)

    # Initially no circulating vehicles -> North approach is clear
    ctrl.update(0.1, pool.active_vehicles)
    assert ctrl.yield_signals[Direction.NORTH] is True

    pool.set_traffic_signals(ctrl.yield_signals)
    pool.update(dt=0.1, elapsed_time=0.1)
    # Clear entry: vehicle should maintain or increase speed
    assert v_enter.acceleration >= 0.0

    # 2. Add circulating vehicle on connection lane in the North conflict zone
    # (theta = pi/4)
    # North incoming end is at (x=-1.75, y=3.5). The connection lane goes from there.
    # Let's create a vehicle on a route that is currently on its connection lane
    route_east = network.generate_route(Direction.EAST, 0, TurnIntent.STRAIGHT)
    v_circ = Vehicle(
        "v_circ",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route_east,
        start_position=105.0,  # 100m incoming + 5m connection
        initial_speed=2.0,
    )
    # Override its coords to be at theta = pi/4 (10.6, 10.6)
    # The controller uses coords directly
    v_circ.update_state(acceleration=0.0, dt=0.0)
    # Inject it into active pool
    pool._active.append(v_circ)

    # Force update its coords to conflict zone (10.606, 10.606)
    # We do a mock override since updating kinematics is route-bound
    object.__setattr__(v_circ, "_position", 102.0)  # connection lane
    v_circ.state = VehicleState.IN_ROUNDABOUT

    from unittest.mock import patch

    original_coords = Vehicle.coords

    class CustomCoordsProperty:
        def __get__(self, obj: Vehicle, obj_type: Any = None) -> tuple[float, float]:
            if obj is None:
                return self  # type: ignore[return-value]
            if obj.vehicle_id == "v_circ":
                return (10.606, 10.606)
            return original_coords.fget(obj)  # type: ignore[meta]

    with patch.object(Vehicle, "coords", CustomCoordsProperty()):
        # Update controller with circulating vehicle present
        ctrl.update(0.1, pool.active_vehicles)
        # With critical gap 6.0 and dist ~11.78m (gap time ~5.89s < 6.0s), should yield
        assert ctrl.yield_signals[Direction.NORTH] is False

    pool.set_traffic_signals(ctrl.yield_signals)
    pool.update(dt=0.1, elapsed_time=0.2)

    # Entering vehicle should now yield/decelerate
    assert v_enter.acceleration < 0.0
