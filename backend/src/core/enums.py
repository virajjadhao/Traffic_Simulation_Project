from enum import Enum


class Direction(str, Enum):
    """Enumeration of intersection approach directions."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
