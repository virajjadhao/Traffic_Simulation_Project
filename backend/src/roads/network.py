from typing import Dict, List

from src.core.enums import Direction, TurnIntent
from src.roads.approach import Approach
from src.roads.lane import Lane


class RoadNetwork:
    """Represents the complete road network topology of the intersection."""

    def __init__(self) -> None:
        """Initialize the RoadNetwork."""
        self._incoming_approaches: Dict[Direction, Approach] = {}
        self._outgoing_approaches: Dict[Direction, Approach] = {}

    def add_incoming_approach(self, approach: Approach) -> None:
        """Add an incoming approach to the network."""
        self._incoming_approaches[approach.direction] = approach

    def add_outgoing_approach(self, approach: Approach) -> None:
        """Add an outgoing approach to the network."""
        self._outgoing_approaches[approach.direction] = approach

    def get_incoming_approach(self, direction: Direction) -> Approach:
        """Get the incoming approach for a given direction."""
        if direction not in self._incoming_approaches:
            raise KeyError(
                f"No incoming approach configured for direction '{direction.value}'."
            )
        return self._incoming_approaches[direction]

    def get_outgoing_approach(self, direction: Direction) -> Approach:
        """Get the outgoing approach for a given direction."""
        if direction not in self._outgoing_approaches:
            raise KeyError(
                f"No outgoing approach configured for direction '{direction.value}'."
            )
        return self._outgoing_approaches[direction]

    def validate_connectivity(self) -> None:
        """Validate that all 4 directions have incoming and outgoing configurations.

        Raises:
            ValueError: If any direction is missing or has zero lanes.
        """
        for direction in Direction:
            if direction not in self._incoming_approaches:
                raise ValueError(
                    f"Missing incoming approach configuration for '{direction.value}'."
                )
            if direction not in self._outgoing_approaches:
                raise ValueError(
                    f"Missing outgoing approach configuration for '{direction.value}'."
                )

            if not self._incoming_approaches[direction].get_lanes():
                raise ValueError(
                    f"Incoming approach for '{direction.value}' has zero lanes."
                )
            if not self._outgoing_approaches[direction].get_lanes():
                raise ValueError(
                    f"Outgoing approach for '{direction.value}' has zero lanes."
                )

    def generate_route(
        self,
        from_direction: Direction,
        lane_index: int,
        turn_intent: TurnIntent,
    ) -> List[Lane]:
        """Generate a complete path of lanes traversing the intersection.

        Args:
            from_direction: Incoming direction of the vehicle.
            lane_index: The index of the lane on the incoming approach.
            turn_intent: Left, straight, or right turn intent.

        Returns:
            A list of 3 sequential Lane segments: [incoming, connection, exit].

        Raises:
            ValueError: If lane_index is out of range or connectivity validation fails.
        """
        self.validate_connectivity()

        incoming_approach = self.get_incoming_approach(from_direction)
        incoming_lanes = incoming_approach.get_lanes()

        if lane_index < 0 or lane_index >= len(incoming_lanes):
            raise ValueError(
                f"Invalid lane index {lane_index} for approach "
                f"'{from_direction.value}'."
            )

        incoming_lane = incoming_lanes[lane_index]

        # Determine target exit direction based on compass turn rules
        direction_map = {
            Direction.NORTH: {
                TurnIntent.LEFT: Direction.EAST,
                TurnIntent.STRAIGHT: Direction.SOUTH,
                TurnIntent.RIGHT: Direction.WEST,
            },
            Direction.SOUTH: {
                TurnIntent.LEFT: Direction.WEST,
                TurnIntent.STRAIGHT: Direction.NORTH,
                TurnIntent.RIGHT: Direction.EAST,
            },
            Direction.EAST: {
                TurnIntent.LEFT: Direction.SOUTH,
                TurnIntent.STRAIGHT: Direction.WEST,
                TurnIntent.RIGHT: Direction.NORTH,
            },
            Direction.WEST: {
                TurnIntent.LEFT: Direction.NORTH,
                TurnIntent.STRAIGHT: Direction.EAST,
                TurnIntent.RIGHT: Direction.SOUTH,
            },
        }

        exit_direction = direction_map[from_direction][turn_intent]
        exit_approach = self.get_outgoing_approach(exit_direction)
        exit_lanes = exit_approach.get_lanes()

        # Match lane index (cap at exit lane count - 1 if mismatched)
        exit_lane_index = min(lane_index, len(exit_lanes) - 1)
        exit_lane = exit_lanes[exit_lane_index]

        # Create virtual connection lane through the intersection box
        conn_id = f"conn_{from_direction.value}_{lane_index}_{turn_intent.value}"
        start_x, start_y = incoming_lane.end_coords
        end_x, end_y = exit_lane.start_coords

        connection_lane = Lane(
            lane_id=conn_id,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            speed_limit=min(incoming_lane.speed_limit, exit_lane.speed_limit),
        )

        return [incoming_lane, connection_lane, exit_lane]

    def setup_default_intersection(
        self,
        approach_length: float = 200.0,
        lane_width: float = 3.5,
        lanes_per_approach: int = 2,
        speed_limit: float = 13.89,
    ) -> None:
        """Convenience builder to layout the default symmetrical 4-way intersection.

        Uses standard right-hand driving coordinates centered at (0, 0).
        """
        # ns_boundary represents the half-width of the East-West road corridor
        ns_boundary = lanes_per_approach * lane_width
        # ew_boundary represents the half-width of the North-South road corridor
        ew_boundary = lanes_per_approach * lane_width

        # Initialize approach structures
        for direction in Direction:
            self.add_incoming_approach(Approach(direction, speed_limit))
            self.add_outgoing_approach(Approach(direction, speed_limit))

        # Build lanes for each direction
        for i in range(lanes_per_approach):
            # i = 0 is innermost lane (closest to center line divider)
            offset = (i + 0.5) * lane_width

            # 1. NORTH
            # Incoming: moves North -> South (downward) on the West side (x < 0)
            self.get_incoming_approach(Direction.NORTH).add_lane(
                Lane(
                    f"n_in_{i}",
                    start_x=-offset,
                    start_y=approach_length,
                    end_x=-offset,
                    end_y=ns_boundary,
                    speed_limit=speed_limit,
                )
            )
            # Outgoing: moves South -> North (upward) on the East side (x > 0)
            self.get_outgoing_approach(Direction.NORTH).add_lane(
                Lane(
                    f"n_out_{i}",
                    start_x=offset,
                    start_y=ns_boundary,
                    end_x=offset,
                    end_y=approach_length,
                    speed_limit=speed_limit,
                )
            )

            # 2. SOUTH
            # Incoming: moves South -> North (upward) on the East side (x > 0)
            self.get_incoming_approach(Direction.SOUTH).add_lane(
                Lane(
                    f"s_in_{i}",
                    start_x=offset,
                    start_y=-approach_length,
                    end_x=offset,
                    end_y=-ns_boundary,
                    speed_limit=speed_limit,
                )
            )
            # Outgoing: moves North -> South (downward) on the West side (x < 0)
            self.get_outgoing_approach(Direction.SOUTH).add_lane(
                Lane(
                    f"s_out_{i}",
                    start_x=-offset,
                    start_y=-ns_boundary,
                    end_x=-offset,
                    end_y=-approach_length,
                    speed_limit=speed_limit,
                )
            )

            # 3. EAST
            # Incoming: moves East -> West (leftward) on the North side (y > 0)
            self.get_incoming_approach(Direction.EAST).add_lane(
                Lane(
                    f"e_in_{i}",
                    start_x=approach_length,
                    start_y=offset,
                    end_x=ew_boundary,
                    end_y=offset,
                    speed_limit=speed_limit,
                )
            )
            # Outgoing: moves West -> East (rightward) on the South side (y < 0)
            self.get_outgoing_approach(Direction.EAST).add_lane(
                Lane(
                    f"e_out_{i}",
                    start_x=ew_boundary,
                    start_y=-offset,
                    end_x=approach_length,
                    end_y=-offset,
                    speed_limit=speed_limit,
                )
            )

            # 4. WEST
            # Incoming: moves West -> East (rightward) on the South side (y < 0)
            self.get_incoming_approach(Direction.WEST).add_lane(
                Lane(
                    f"w_in_{i}",
                    start_x=-approach_length,
                    start_y=-offset,
                    end_x=-ew_boundary,
                    end_y=-offset,
                    speed_limit=speed_limit,
                )
            )
            # Outgoing: moves East -> West (leftward) on the North side (y > 0)
            self.get_outgoing_approach(Direction.WEST).add_lane(
                Lane(
                    f"w_out_{i}",
                    start_x=-ew_boundary,
                    start_y=offset,
                    end_x=-approach_length,
                    end_y=offset,
                    speed_limit=speed_limit,
                )
            )
