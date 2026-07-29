import math
import random
from typing import Dict, List, Optional

from src.core.enums import Direction, TurnIntent
from src.roads.network import RoadNetwork
from src.vehicles.vehicle import Vehicle

# Default directional split: equal across all 4 directions
_DEFAULT_DIRECTIONAL_SPLIT: Dict[str, float] = {
    "north": 0.25,
    "south": 0.25,
    "east": 0.25,
    "west": 0.25,
}

# Default turn probabilities
_DEFAULT_TURN_PROBABILITIES: Dict[str, float] = {
    "left": 0.2,
    "straight": 0.6,
    "right": 0.2,
}

# Direction name to enum mapping
_DIR_MAP: Dict[str, Direction] = {
    "north": Direction.NORTH,
    "south": Direction.SOUTH,
    "east": Direction.EAST,
    "west": Direction.WEST,
}

# Turn name to enum mapping
_TURN_MAP: Dict[str, TurnIntent] = {
    "left": TurnIntent.LEFT,
    "straight": TurnIntent.STRAIGHT,
    "right": TurnIntent.RIGHT,
}


class VehicleSpawner:
    """Generates vehicles on approach lanes using configurable arrival distributions."""

    def __init__(
        self,
        network: RoadNetwork,
        arrival_rate: float = 0.5,
        total_vehicles: int = 200,
        arrival_distribution: str = "poisson",
        directional_split: Optional[Dict[str, float]] = None,
        turn_probabilities: Optional[Dict[str, float]] = None,
        random_seed: int = 42,
        vehicle_length: float = 4.5,
        vehicle_width: float = 2.0,
        desired_speed: float = 13.89,
        minimum_gap: float = 2.0,
    ) -> None:
        """Initialize the VehicleSpawner.

        Args:
            network: The road network to spawn vehicles into.
            arrival_rate: Mean vehicles arriving per second.
            total_vehicles: Maximum vehicles to generate.
            arrival_distribution: "poisson" or "uniform".
            directional_split: Fraction of vehicles from each direction.
            turn_probabilities: Turn intent probabilities.
            random_seed: RNG seed for reproducibility.
            vehicle_length: Default length of spawned vehicles (m).
            vehicle_width: Default width of spawned vehicles (m).
            desired_speed: Default desired speed (m/s).
            minimum_gap: Minimum gap required at lane entrance (m).

        Raises:
            ValueError: If arrival_rate or total_vehicles are invalid.
        """
        if arrival_rate <= 0:
            raise ValueError("Arrival rate must be positive.")
        if total_vehicles <= 0:
            raise ValueError("Total vehicles must be positive.")
        if arrival_distribution not in ("poisson", "uniform"):
            raise ValueError("Arrival distribution must be 'poisson' or 'uniform'.")
        if vehicle_length <= 0 or vehicle_width <= 0:
            raise ValueError("Vehicle dimensions must be positive.")
        if desired_speed <= 0:
            raise ValueError("Desired speed must be positive.")
        if minimum_gap < 0:
            raise ValueError("Minimum gap cannot be negative.")

        self._network: RoadNetwork = network
        self._arrival_rate: float = arrival_rate
        self._total_vehicles: int = total_vehicles
        self._arrival_distribution: str = arrival_distribution
        self._vehicle_length: float = vehicle_length
        self._vehicle_width: float = vehicle_width
        self._desired_speed: float = desired_speed
        self._minimum_gap: float = minimum_gap

        # Parse directional split
        split = directional_split or _DEFAULT_DIRECTIONAL_SPLIT
        self._dir_names: List[str] = list(split.keys())
        self._dir_weights: List[float] = list(split.values())

        # Parse turn probabilities
        turns = turn_probabilities or _DEFAULT_TURN_PROBABILITIES
        self._turn_names: List[str] = list(turns.keys())
        self._turn_weights: List[float] = list(turns.values())

        # Seeded RNG for reproducibility
        self._rng: random.Random = random.Random(random_seed)

        # Spawning state
        self._spawned_count: int = 0
        self._next_spawn_time: float = self._sample_interval()

    def _sample_interval(self) -> float:
        """Sample the next inter-arrival time based on distribution type."""
        if self._arrival_distribution == "poisson":
            u = self._rng.random()
            return -math.log(u) / self._arrival_rate
        # uniform: constant interval
        return 1.0 / self._arrival_rate

    def _pick_direction(self) -> Direction:
        """Pick a random direction weighted by directional split."""
        chosen = self._rng.choices(self._dir_names, weights=self._dir_weights, k=1)[0]
        return _DIR_MAP[chosen]

    def _pick_turn_intent(self) -> TurnIntent:
        """Pick a random turn intent weighted by probabilities."""
        chosen = self._rng.choices(self._turn_names, weights=self._turn_weights, k=1)[0]
        return _TURN_MAP[chosen]

    def _is_lane_clear(
        self,
        vehicles_on_lane: List[Vehicle],
    ) -> bool:
        """Check if there is enough headway at the start of a lane.

        Args:
            vehicles_on_lane: Current vehicles on the target lane.

        Returns:
            True if safe to spawn at position 0.
        """
        if not vehicles_on_lane:
            return True
        closest = min(vehicles_on_lane, key=lambda v: v.position)
        rear_of_closest = closest.position - closest.length / 2.0
        required_clearance = self._minimum_gap + self._vehicle_length
        return rear_of_closest >= required_clearance

    def try_spawn(self, elapsed_time: float) -> Optional[Vehicle]:
        """Attempt to spawn a vehicle if the arrival time has been reached.

        Args:
            elapsed_time: Current simulation elapsed time in seconds.

        Returns:
            The newly spawned Vehicle, or None if not yet time or blocked.
        """
        if self._spawned_count >= self._total_vehicles:
            return None
        if elapsed_time < self._next_spawn_time:
            return None

        direction = self._pick_direction()
        turn_intent = self._pick_turn_intent()
        incoming = self._network.get_incoming_approach(direction)
        lanes = incoming.get_lanes()
        lane_index = self._rng.randint(0, len(lanes) - 1)

        if not self._is_lane_clear(lanes[lane_index].get_vehicles()):
            # Reschedule slightly later
            self._next_spawn_time = elapsed_time + self._sample_interval()
            return None

        route = self._network.generate_route(direction, lane_index, turn_intent)
        vehicle_id = f"veh_{self._spawned_count}"
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            length=self._vehicle_length,
            width=self._vehicle_width,
            desired_speed=self._desired_speed,
            route=route,
            start_position=0.0,
            initial_speed=0.0,
        )

        self._spawned_count += 1
        self._next_spawn_time = elapsed_time + self._sample_interval()
        return vehicle

    @property
    def spawned_count(self) -> int:
        """Get the total number of vehicles spawned so far."""
        return self._spawned_count

    @property
    def is_exhausted(self) -> bool:
        """Check if the spawner has reached its vehicle limit."""
        return self._spawned_count >= self._total_vehicles
