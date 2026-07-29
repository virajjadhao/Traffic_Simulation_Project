from typing import Dict, List, Optional

from src.core.enums import Direction, VehicleState
from src.intersection.conflict_zones import ConflictZoneDetector
from src.vehicles.idm import IntelligentDriverModel
from src.vehicles.router import find_leader
from src.vehicles.spawner import VehicleSpawner
from src.vehicles.vehicle import Vehicle


class VehiclePool:
    """Manages the active and exited vehicle collections."""

    def __init__(
        self,
        spawner: VehicleSpawner,
        idm: IntelligentDriverModel,
        traffic_signals: Optional[Dict[Direction, bool]] = None,
        conflict_detector: Optional[ConflictZoneDetector] = None,
    ) -> None:
        """Initialize the VehiclePool.

        Args:
            spawner: The vehicle spawner instance.
            idm: The Intelligent Driver Model for acceleration.
            traffic_signals: Optional signal state map (True=green).
            conflict_detector: Optional conflict zone safety detector.
        """
        self._spawner: VehicleSpawner = spawner
        self._idm: IntelligentDriverModel = idm
        self._traffic_signals: Optional[Dict[Direction, bool]] = traffic_signals
        self._conflict_detector: ConflictZoneDetector = (
            conflict_detector or ConflictZoneDetector()
        )
        self._active: List[Vehicle] = []
        self._exited: List[Vehicle] = []

    def update(self, dt: float, elapsed_time: float) -> None:
        """Execute one simulation tick for all vehicles.

        Steps:
            1. Try to spawn a new vehicle.
            2. For each active vehicle, find leader and compute IDM acceleration.
            3. Update each vehicle's kinematics.
            4. Move exited vehicles from active to exited list.

        Args:
            dt: Time step duration in seconds.
            elapsed_time: Current simulation elapsed time in seconds.
        """
        # 1. Spawn
        new_vehicle = self._spawner.try_spawn(elapsed_time)
        if new_vehicle is not None:
            self._active.append(new_vehicle)

        # 2 & 3. Update each active vehicle
        for vehicle in self._active:
            if vehicle.state == VehicleState.EXITED:
                continue
            leader, gap = find_leader(vehicle, self._traffic_signals)
            lead_speed = leader.speed if leader is not None else None
            gap_val = gap if leader is not None else None
            acc_lane = self._idm.calculate_acceleration(
                speed=vehicle.speed,
                desired_speed=vehicle.desired_speed,
                lead_speed=lead_speed,
                gap=gap_val,
            )

            # Check for crossing conflict constraints
            conflict_gap = self._conflict_detector.check_conflicts(
                vehicle, self._active
            )
            if conflict_gap < float("inf"):
                acc_conflict = self._idm.calculate_acceleration(
                    speed=vehicle.speed,
                    desired_speed=vehicle.desired_speed,
                    lead_speed=0.0,  # Treat as stationary virtual obstacle
                    gap=conflict_gap,
                )
                acceleration = min(acc_lane, acc_conflict)
            else:
                acceleration = acc_lane

            vehicle.update_state(acceleration, dt)

        # 4. Cleanup exited vehicles
        still_active: List[Vehicle] = []
        for vehicle in self._active:
            if vehicle.state == VehicleState.EXITED:
                self._exited.append(vehicle)
            else:
                still_active.append(vehicle)
        self._active = still_active

    def set_traffic_signals(
        self,
        signals: Dict[Direction, bool],
    ) -> None:
        """Update the traffic signal state map.

        Args:
            signals: Dict mapping Direction to green (True) or red (False).
        """
        self._traffic_signals = signals

    @property
    def active_vehicles(self) -> List[Vehicle]:
        """Get a copy of the active vehicles list."""
        return list(self._active)

    @property
    def exited_vehicles(self) -> List[Vehicle]:
        """Get a copy of the exited vehicles list."""
        return list(self._exited)

    @property
    def active_count(self) -> int:
        """Get the number of currently active vehicles."""
        return len(self._active)

    @property
    def exited_count(self) -> int:
        """Get the number of exited vehicles."""
        return len(self._exited)

    def get_counts_by_state(self) -> Dict[VehicleState, int]:
        """Count vehicles grouped by VehicleState.

        Returns:
            Dict mapping each VehicleState to the count of vehicles.
        """
        counts: Dict[VehicleState, int] = {s: 0 for s in VehicleState}
        for v in self._active:
            counts[v.state] += 1
        counts[VehicleState.EXITED] = len(self._exited)
        return counts
