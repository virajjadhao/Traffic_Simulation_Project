import pytest

from src.intersection.geometry import IntersectionGeometry


def test_intersection_geometry_initialization() -> None:
    # Test valid initialization
    geom = IntersectionGeometry(center=(0.0, 0.0), radius=20.0)
    assert geom.center == (0.0, 0.0)
    assert geom.radius == 20.0

    # Test invalid initialization
    with pytest.raises(ValueError, match="Bounding radius must be greater than zero"):
        IntersectionGeometry(center=(0.0, 0.0), radius=0.0)

    with pytest.raises(ValueError, match="Bounding radius must be greater than zero"):
        IntersectionGeometry(center=(1.0, -1.0), radius=-5.0)


def test_is_within_intersection() -> None:
    geom = IntersectionGeometry(center=(10.0, 20.0), radius=10.0)

    # Center is inside
    assert geom.is_within_intersection(10.0, 20.0) is True

    # Inside boundary
    assert geom.is_within_intersection(15.0, 20.0) is True
    assert geom.is_within_intersection(10.0, 28.0) is True

    # On boundary
    assert geom.is_within_intersection(10.0, 30.0) is True
    assert geom.is_within_intersection(0.0, 20.0) is True

    # Just outside boundary
    assert geom.is_within_intersection(10.0, 30.01) is False
    assert geom.is_within_intersection(-0.01, 20.0) is False

    # Diagonally inside vs outside
    # Distance from center: math.hypot(7, 7) = 9.899 < 10
    assert geom.is_within_intersection(17.0, 27.0) is True
    # Distance from center: math.hypot(8, 8) = 11.31 > 10
    assert geom.is_within_intersection(18.0, 28.0) is False


def test_approach_lane_mapping() -> None:
    geom = IntersectionGeometry(center=(0.0, 0.0), radius=15.0)

    # Register approach lane
    geom.map_approach_lane("n_in_0", (0.0, 15.0))
    geom.map_approach_lane("s_in_0", (0.0, -15.0))

    # Retrieve coordinates
    assert geom.get_crossing_start("n_in_0") == (0.0, 15.0)
    assert geom.get_crossing_start("s_in_0") == (0.0, -15.0)

    # KeyError for unmapped lane
    with pytest.raises(KeyError, match="Approach lane 'w_in_0' is not mapped"):
        geom.get_crossing_start("w_in_0")


def test_exit_lane_mapping() -> None:
    geom = IntersectionGeometry(center=(0.0, 0.0), radius=15.0)

    # Register exit lanes
    geom.map_exit_lane((15.0, 0.0), "e_out_0")
    geom.map_exit_lane((-15.0, 0.0), "w_out_0")

    # Retrieve exit lanes
    assert geom.get_exit_lane((15.0, 0.0)) == "e_out_0"
    assert geom.get_exit_lane((-15.0, 0.0)) == "w_out_0"

    # KeyError for unmapped coordinates
    with pytest.raises(KeyError, match="No exit lane mapped for coordinates"):
        geom.get_exit_lane((0.0, 0.0))


def test_floating_point_lookup_tolerance() -> None:
    geom = IntersectionGeometry(center=(0.0, 0.0), radius=15.0)

    # Map with floating point coordinates
    geom.map_exit_lane((1.7500000000000002, -7.0000000000000001), "e_out_0")

    # Lookup with slight representation discrepancy
    assert geom.get_exit_lane((1.75, -7.0)) == "e_out_0"
    # Even with very small offset (within 6 decimal places)
    assert geom.get_exit_lane((1.7500001, -7.0)) == "e_out_0"

    # Should raise KeyError for significant difference
    with pytest.raises(KeyError):
        geom.get_exit_lane((1.75001, -7.0))
