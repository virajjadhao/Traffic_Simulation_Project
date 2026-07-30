from src.metrics.definitions.idle_loss import IdleOpportunityLossTracker


def test_idle_loss_tracker_init_and_reset() -> None:
    """Verify tracker initialization and reset functionality."""
    tracker = IdleOpportunityLossTracker()
    assert tracker._iol_ticks == 0
    assert tracker._total_ticks == 0

    tracker.record_tick("fixed_time_signal", [], {"north": 1})
    tracker.reset()
    assert tracker._iol_ticks == 0
    assert tracker._total_ticks == 0


def test_idle_loss_tracker_roundabout() -> None:
    """Verify roundabout always records IOL of 0.0."""
    tracker = IdleOpportunityLossTracker()

    # Even if queue is present and signals are empty, roundabout should
    # return False for IOL tick
    is_iol = tracker.record_tick(
        controller_type="roundabout",
        signals=[],
        queue_lengths={"north": 3, "south": 2},
    )
    assert is_iol is False

    res = tracker.calculate_metric()
    assert res["value"] == 0.0
    assert res["unit"] == "dimensionless"


def test_idle_loss_tracker_signal_logic() -> None:
    """Verify IOL conditions mapping under signal signals and queues."""
    tracker = IdleOpportunityLossTracker()

    # T1: ns_green active (North/South green), ew_red active (East/West red).
    # Queues: north=0, south=0, east=2, west=0.
    # Result: Green directions empty (north=0, south=0) AND red direction
    # has queue (east=2). Should count as IOL.
    signals_t1 = [
        {"direction": "north", "color": "green"},
        {"direction": "south", "color": "green"},
        {"direction": "east", "color": "red"},
        {"direction": "west", "color": "red"},
    ]
    is_iol_t1 = tracker.record_tick(
        "fixed_time_signal", signals_t1, {"north": 0, "south": 0, "east": 2}
    )
    assert is_iol_t1 is True

    # T2: ns_green active (North/South green).
    # Queues: north=1, south=0, east=2.
    # Result: Green direction has queue (north=1). Should NOT count as IOL.
    is_iol_t2 = tracker.record_tick(
        "fixed_time_signal", signals_t1, {"north": 1, "south": 0, "east": 2}
    )
    assert is_iol_t2 is False

    # T3: ns_green active (North/South green).
    # Queues: north=0, south=0, east=0.
    # Result: Green empty (north=0, south=0) but red ALSO empty (east=0).
    # Should NOT count as IOL.
    is_iol_t3 = tracker.record_tick(
        "fixed_time_signal", signals_t1, {"north": 0, "south": 0, "east": 0}
    )
    assert is_iol_t3 is False

    # T4: all_red phase.
    # Queues: north=1, south=0, east=0.
    # Result: Green empty (none are green) AND red has queue (north=1).
    # Should count as IOL.
    signals_t4 = [
        {"direction": "north", "color": "red"},
        {"direction": "south", "color": "red"},
        {"direction": "east", "color": "red"},
        {"direction": "west", "color": "red"},
    ]
    is_iol_t4 = tracker.record_tick("fixed_time_signal", signals_t4, {"north": 1})
    assert is_iol_t4 is True

    # Calculate metric: 2 IOL ticks out of 4 ticks = 0.5
    res = tracker.calculate_metric()
    assert res["value"] == 0.5
    assert res["unit"] == "dimensionless"
