from enum import Enum


class Direction(str, Enum):
    """Enumeration of intersection approach directions."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class VehicleState(str, Enum):
    """Enumeration of vehicle states during simulation."""

    APPROACHING = "approaching"
    WAITING = "waiting"
    CROSSING = "crossing"
    IN_ROUNDABOUT = "in_roundabout"
    EXITED = "exited"
