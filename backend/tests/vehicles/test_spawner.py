import pytest

from src.roads.network import RoadNetwork
from src.vehicles.spawner import VehicleSpawner


def _make_network() -> RoadNetwork:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=2,
    )
    return net


@pytest.fixture
def network() -> RoadNetwork:
    return _make_network()


def test_spawner_initialization(network: RoadNetwork) -> None:
    spawner = VehicleSpawner(network, arrival_rate=1.0, total_vehicles=50)
    assert spawner.spawned_count == 0
    assert not spawner.is_exhausted


def test_spawner_invalid_initialization(network: RoadNetwork) -> None:
    with pytest.raises(ValueError, match="Arrival rate must be positive"):
        VehicleSpawner(network, arrival_rate=0.0)
    with pytest.raises(ValueError, match="Total vehicles must be positive"):
        VehicleSpawner(network, total_vehicles=0)
    with pytest.raises(ValueError, match="'poisson' or 'uniform'"):
        VehicleSpawner(network, arrival_distribution="burst")


def test_spawner_deterministic() -> None:
    """Same seed should produce same spawn sequence on independent networks."""
    net_a = _make_network()
    net_b = _make_network()
    spawner_a = VehicleSpawner(
        net_a, arrival_rate=2.0, total_vehicles=5, random_seed=123
    )
    spawner_b = VehicleSpawner(
        net_b, arrival_rate=2.0, total_vehicles=5, random_seed=123
    )

    results_a = []
    results_b = []
    for t in range(200):
        elapsed = t * 0.1
        va = spawner_a.try_spawn(elapsed)
        vb = spawner_b.try_spawn(elapsed)
        if va is not None:
            results_a.append(va.vehicle_id)
        if vb is not None:
            results_b.append(vb.vehicle_id)

    assert len(results_a) > 0
    assert results_a == results_b


def test_spawner_total_cap(network: RoadNetwork) -> None:
    """Spawning should stop after total_vehicles is reached."""
    spawner = VehicleSpawner(
        network, arrival_rate=100.0, total_vehicles=3, random_seed=42
    )

    vehicles = []
    for t in range(1000):
        v = spawner.try_spawn(t * 0.1)
        if v is not None:
            vehicles.append(v)

    assert len(vehicles) == 3
    assert spawner.is_exhausted
    assert spawner.spawned_count == 3

    # Further spawns should return None
    assert spawner.try_spawn(1000.0) is None


def test_spawner_safety_headway(network: RoadNetwork) -> None:
    """Should not spawn if lane entrance is blocked."""
    spawner = VehicleSpawner(
        network,
        arrival_rate=100.0,
        total_vehicles=10,
        random_seed=42,
        directional_split={"north": 1.0, "south": 0.0, "east": 0.0, "west": 0.0},
    )

    # Spawn first vehicle (use large elapsed time to ensure past interval)
    v1 = spawner.try_spawn(10.0)
    assert v1 is not None
    assert v1.position == 0.0
    # v1 is at position 0, blocking the lane entrance.
    # Next spawn attempt should be blocked because vehicle rear
    # is at -2.25 which is < minimum_gap + vehicle_length = 6.5
    v2 = spawner.try_spawn(10.001)
    assert v2 is None


def test_spawner_directional_split(network: RoadNetwork) -> None:
    """With north=1.0, all vehicles should come from north."""
    spawner = VehicleSpawner(
        network,
        arrival_rate=10.0,
        total_vehicles=5,
        random_seed=42,
        directional_split={
            "north": 1.0,
            "south": 0.0,
            "east": 0.0,
            "west": 0.0,
        },
    )

    vehicles = []
    for t in range(500):
        v = spawner.try_spawn(t * 0.1)
        if v is not None:
            vehicles.append(v)

    assert len(vehicles) > 0
    for v in vehicles:
        # All vehicles should be on north incoming lanes
        assert v.route[0].lane_id.startswith("n_in")


def test_spawner_uniform_distribution(network: RoadNetwork) -> None:
    """Uniform distribution should produce constant intervals."""
    spawner = VehicleSpawner(
        network,
        arrival_rate=2.0,
        total_vehicles=5,
        arrival_distribution="uniform",
        random_seed=42,
    )

    # With rate=2.0, interval=0.5s. First spawn at t=0.5
    assert spawner.try_spawn(0.0) is None
    assert spawner.try_spawn(0.4) is None
    v1 = spawner.try_spawn(0.5)
    assert v1 is not None
    # Next spawn at t=1.0
    assert spawner.try_spawn(0.9) is None
    v2 = spawner.try_spawn(1.0)
    assert v2 is not None
