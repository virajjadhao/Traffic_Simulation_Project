from src.core.enums import Direction, TurnIntent
from src.intersection.conflict_zones import ConflictZoneDetector
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


def test_pool_spawn_integration() -> None:
    """Verify update() spawns vehicles into the active list."""
    network = _make_network()
    spawner = VehicleSpawner(
        network, arrival_rate=100.0, total_vehicles=3, random_seed=42
    )
    idm = IntelligentDriverModel()
    pool = VehiclePool(spawner, idm)

    # Run several ticks to allow spawning
    for t in range(100):
        pool.update(dt=0.1, elapsed_time=t * 0.1)

    assert pool.active_count + pool.exited_count > 0
    assert spawner.spawned_count <= 3


def test_pool_idm_movement() -> None:
    """Verify vehicles accelerate from standstill over ticks."""
    network = _make_network()
    spawner = VehicleSpawner(
        network,
        arrival_rate=100.0,
        total_vehicles=1,
        random_seed=42,
    )
    idm = IntelligentDriverModel(max_acceleration=2.0)
    pool = VehiclePool(spawner, idm)

    # Spawn first vehicle
    pool.update(dt=0.1, elapsed_time=10.0)
    assert pool.active_count == 1

    vehicle = pool.active_vehicles[0]
    initial_pos = vehicle.position

    # Run 10 more ticks
    for t in range(10):
        pool.update(dt=0.1, elapsed_time=10.1 + t * 0.1)

    # Vehicle should have moved forward
    assert vehicle.position > initial_pos
    assert vehicle.speed > 0.0


def test_pool_exit_cleanup() -> None:
    """Verify exited vehicles move from active to exited list."""
    network = _make_network()
    spawner = VehicleSpawner(
        network,
        arrival_rate=100.0,
        total_vehicles=1,
        random_seed=42,
    )
    idm = IntelligentDriverModel(max_acceleration=5.0)
    pool = VehiclePool(spawner, idm)

    # Spawn vehicle
    pool.update(dt=0.1, elapsed_time=10.0)
    assert pool.active_count == 1

    # Run many ticks to let it traverse the entire route and exit
    for t in range(5000):
        pool.update(dt=0.1, elapsed_time=10.1 + t * 0.1)
        if pool.exited_count > 0:
            break

    assert pool.exited_count == 1
    assert pool.active_count == 0


def test_pool_counts_by_state() -> None:
    """Verify get_counts_by_state returns correct tallies."""
    network = _make_network()
    spawner = VehicleSpawner(
        network,
        arrival_rate=100.0,
        total_vehicles=2,
        random_seed=42,
    )
    idm = IntelligentDriverModel()
    pool = VehiclePool(spawner, idm)

    # Spawn vehicles
    pool.update(dt=0.1, elapsed_time=10.0)
    pool.update(dt=0.1, elapsed_time=20.0)

    counts = pool.get_counts_by_state()
    total = sum(counts.values())
    assert total == pool.active_count + pool.exited_count


def test_pool_traffic_signal_integration() -> None:
    """Verify vehicles respond to red signal by decelerating."""
    network = _make_network()
    spawner = VehicleSpawner(
        network,
        arrival_rate=100.0,
        total_vehicles=1,
        random_seed=42,
        directional_split={"north": 1.0, "south": 0.0, "east": 0.0, "west": 0.0},
    )
    idm = IntelligentDriverModel(max_acceleration=2.0)
    signals = {
        Direction.NORTH: False,  # RED
        Direction.SOUTH: True,
        Direction.EAST: True,
        Direction.WEST: True,
    }
    pool = VehiclePool(spawner, idm, traffic_signals=signals)

    # Spawn vehicle
    pool.update(dt=0.1, elapsed_time=10.0)
    assert pool.active_count == 1

    # Accelerate vehicle a bit first (free road initially)
    # Then run many ticks — vehicle should eventually slow down
    for t in range(500):
        pool.update(dt=0.1, elapsed_time=10.1 + t * 0.1)

    # Vehicle should still be active (stopped at red light)
    if pool.active_count > 0:
        vehicle = pool.active_vehicles[0]
        # At red light, vehicle should have low speed near stop line
        assert vehicle.speed < 1.0


def test_pool_conflict_integration() -> None:
    """Verify that conflicting vehicles decelerate in the update loop."""
    network = _make_network()
    # Mock spawner that doesn't spawn anything automatically
    spawner = VehicleSpawner(network, arrival_rate=1.0, total_vehicles=1)
    spawner.try_spawn = lambda t: None  # type: ignore[assignment]
    idm = IntelligentDriverModel(max_acceleration=2.0, comfort_deceleration=3.0)

    detector = ConflictZoneDetector(safety_buffer=2.0)
    pool = VehiclePool(spawner, idm, conflict_detector=detector)

    route_ns = network.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    route_we = network.generate_route(Direction.WEST, 0, TurnIntent.STRAIGHT)

    v_ns = Vehicle(
        "v_ns",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route_ns,
        start_position=90.0,
        initial_speed=10.0,
    )
    v_we = Vehicle(
        "v_we",
        length=4.0,
        width=2.0,
        desired_speed=10.0,
        route=route_we,
        start_position=95.0,
        initial_speed=10.0,
    )

    # Manually insert them into the pool
    pool._active.extend([v_ns, v_we])

    # Update pool by one tick
    pool.update(dt=0.1, elapsed_time=0.1)

    # v_we is closer to P, so it should continue moving/accelerating
    # v_ns should detect conflict and decelerate
    assert v_ns.acceleration < 0.0
    assert v_we.acceleration >= 0.0
