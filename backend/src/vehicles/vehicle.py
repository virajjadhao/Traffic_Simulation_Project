import math
from typing import TYPE_CHECKING, List, Optional, Tuple

from src.core.enums import VehicleState
from src.roads.lane import Lane

if TYPE_CHECKING:
    # Avoid circular imports at runtime
    pass


class Vehicle:
    """Represents a vehicle moving along a lane corridor path in the simulation."""

    def __init__(
        self,
        vehicle_id: str,
        length: float,
        width: float,
        desired_speed: float,
        route: List[Lane],
        start_position: float = 0.0,
        initial_speed: float = 0.0,
    ) -> None:
        """Initialize the Vehicle.

        Args:
            vehicle_id: Unique identifier for the vehicle.
            length: Physical length of the vehicle (meters).
            width: Physical width of the vehicle (meters).
            desired_speed: Target free-flow speed of the vehicle (m/s).
            route: List of Lane corridors defining the path of the vehicle.
            start_position: Initial position along the first lane (meters).
            initial_speed: Initial speed of the vehicle (m/s).

        Raises:
            ValueError: If inputs are invalid (dimensions <= 0, empty route,
                negative speeds).
        """
        if not route:
            raise ValueError("Vehicle route cannot be empty.")
        if length <= 0 or width <= 0:
            raise ValueError("Vehicle dimensions (length, width) must be positive.")
        if desired_speed <= 0:
            raise ValueError("Desired speed must be positive.")
        if initial_speed < 0:
            raise ValueError("Initial speed cannot be negative.")
        if start_position < 0:
            raise ValueError("Start position cannot be negative.")

        self._vehicle_id: str = vehicle_id
        self._length: float = length
        self._width: float = width
        self._desired_speed: float = desired_speed
        self._route: List[Lane] = list(route)

        # Route tracking
        self._current_lane_index: int = 0
        self._position: float = start_position

        # Kinematics
        self._speed: float = initial_speed
        self._acceleration: float = 0.0

        # Telemetry and state tracking
        self._state: VehicleState = VehicleState.APPROACHING
        self._cumulative_wait_time: float = 0.0
        self._stop_count: int = 0
        self._is_stopped: bool = False

        # Override properties for control strategies (e.g. roundabout)
        self._coords_override: Optional[Tuple[float, float]] = None
        self._heading_override: Optional[float] = None
        self._speed_limit_override: Optional[float] = None

        # Timestamps for metric analysis
        self._spawn_time: Optional[float] = None
        self._exit_time: Optional[float] = None

        # Add vehicle to initial lane
        self.lane.add_vehicle(self)

        # Perform initial state-based stop check
        if self._speed < 0.1:  # default stopSpeedThreshold
            self._is_stopped = True
            self._stop_count = 1

        if self._speed < 0.5:  # default waitSpeedThreshold
            self._state = VehicleState.WAITING

    @property
    def vehicle_id(self) -> str:
        """Get the vehicle ID."""
        return self._vehicle_id

    @property
    def length(self) -> float:
        """Get the vehicle length."""
        return self._length

    @property
    def width(self) -> float:
        """Get the vehicle width."""
        return self._width

    @property
    def desired_speed(self) -> float:
        """Get the vehicle's desired speed."""
        if self._speed_limit_override is not None:
            return self._speed_limit_override
        return self._desired_speed

    @property
    def route(self) -> List[Lane]:
        """Get the full route sequence of lanes."""
        return list(self._route)

    @property
    def lane(self) -> Lane:
        """Get the current lane the vehicle is on."""
        return self._route[self._current_lane_index]

    @property
    def current_lane_index(self) -> int:
        """Get the index of the current lane in the route."""
        return self._current_lane_index

    @property
    def position(self) -> float:
        """Get the distance along the current lane (meters)."""
        return self._position

    @property
    def speed(self) -> float:
        """Get the current speed (m/s)."""
        return self._speed

    @property
    def acceleration(self) -> float:
        """Get the current acceleration (m/s^2)."""
        return self._acceleration

    @property
    def state(self) -> VehicleState:
        """Get the current vehicle state."""
        return self._state

    @state.setter
    def state(self, new_state: VehicleState) -> None:
        """Set the vehicle state externally (e.g. crossing, roundabout)."""
        self._state = new_state

    @property
    def wait_time(self) -> float:
        """Get cumulative wait time in seconds."""
        return self._cumulative_wait_time

    @property
    def stop_count(self) -> int:
        """Get total number of stops."""
        return self._stop_count

    @property
    def coords(self) -> Tuple[float, float]:
        """Get the (x, y) coordinates of the vehicle center."""
        if self._coords_override is not None:
            return self._coords_override
        if self._state == VehicleState.EXITED:
            # Return end coords of last lane if exited
            return self._route[-1].end_coords
        return self.lane.get_point_at_distance(self._position)

    @property
    def x(self) -> float:
        """Get the X coordinate of the vehicle center."""
        return self.coords[0]

    @property
    def y(self) -> float:
        """Get the Y coordinate of the vehicle center."""
        return self.coords[1]

    @property
    def heading(self) -> float:
        """Get the heading angle of the vehicle in degrees."""
        if self._heading_override is not None:
            return self._heading_override
        if self._state == VehicleState.EXITED:
            return self._route[-1].heading
        return self.lane.heading

    @property
    def lane_id(self) -> str:
        """Get the lane ID string, or empty if exited."""
        if self._state == VehicleState.EXITED:
            return ""
        return self.lane.lane_id

    def get_bounding_box(self) -> List[Tuple[float, float]]:
        """Compute coordinates of the 4 corners of the vehicle bounding box.

        Returns:
            List of 4 tuples: [Front-Left, Front-Right, Rear-Right, Rear-Left].
        """
        cx, cy = self.coords
        heading_rad = math.radians(self.heading)

        # Forward unit vector (along heading)
        fx, fy = math.sin(heading_rad), math.cos(heading_rad)
        # Perpendicular right unit vector
        rx, ry = fy, -fx

        half_l = 0.5 * self._length
        half_w = 0.5 * self._width

        # Corners offsets
        fl = (cx + half_l * fx - half_w * rx, cy + half_l * fy - half_w * ry)
        fr = (cx + half_l * fx + half_w * rx, cy + half_l * fy + half_w * ry)
        rr = (cx - half_l * fx + half_w * rx, cy - half_l * fy + half_w * ry)
        rl = (cx - half_l * fx - half_w * rx, cy - half_l * fy - half_w * ry)

        return [fl, fr, rr, rl]

    @property
    def coords_override(self) -> Optional[Tuple[float, float]]:
        """Get the coordinate override tuple."""
        return self._coords_override

    @coords_override.setter
    def coords_override(self, val: Optional[Tuple[float, float]]) -> None:
        """Set the coordinate override tuple."""
        self._coords_override = val

    @property
    def heading_override(self) -> Optional[float]:
        """Get the heading override angle in degrees."""
        return self._heading_override

    @heading_override.setter
    def heading_override(self, val: Optional[float]) -> None:
        """Set the heading override angle in degrees."""
        self._heading_override = val

    @property
    def speed_limit_override(self) -> Optional[float]:
        """Get the speed limit override in m/s."""
        return self._speed_limit_override

    @speed_limit_override.setter
    def speed_limit_override(self, val: Optional[float]) -> None:
        """Set the speed limit override in m/s."""
        self._speed_limit_override = val

    @property
    def spawn_time(self) -> Optional[float]:
        """Get the simulation time when the vehicle was spawned."""
        return self._spawn_time

    @spawn_time.setter
    def spawn_time(self, val: Optional[float]) -> None:
        """Set the spawn time of the vehicle."""
        self._spawn_time = val

    @property
    def exit_time(self) -> Optional[float]:
        """Get the simulation time when the vehicle exited."""
        return self._exit_time

    @exit_time.setter
    def exit_time(self, val: Optional[float]) -> None:
        """Set the exit time of the vehicle."""
        self._exit_time = val

    def update_state(
        self,
        acceleration: float,
        dt: float,
        wait_speed_threshold: float = 0.5,
        stop_speed_threshold: float = 0.1,
    ) -> None:
        """Advance the vehicle's position, speed, and status indicators.

        Args:
            acceleration: Acceleration value to apply (m/s^2).
            dt: Time step duration (seconds).
            wait_speed_threshold: Speed threshold for waiting time (m/s).
            stop_speed_threshold: Speed threshold for stop counting (m/s).
        """
        if self._state == VehicleState.EXITED:
            return

        self._acceleration = acceleration

        # Euler-Cromer Integration
        self._speed = max(0.0, self._speed + acceleration * dt)
        self._position += self._speed * dt

        # Hysteresis-based Stop Count & Wait Time tracking
        if self._speed < stop_speed_threshold:
            if not self._is_stopped:
                self._stop_count += 1
                self._is_stopped = True
        elif self._speed >= 2 * stop_speed_threshold:
            self._is_stopped = False

        if self._speed < wait_speed_threshold:
            self._cumulative_wait_time += dt
            if self._state == VehicleState.APPROACHING:
                self._state = VehicleState.WAITING
        else:
            if self._state == VehicleState.WAITING:
                self._state = VehicleState.APPROACHING

        # Handle Lane Transitions along the route
        while self._position >= self.lane.length:
            if self._current_lane_index + 1 < len(self._route):
                # Transition to next lane
                self._position -= self.lane.length
                self.lane.remove_vehicle(self)
                self._current_lane_index += 1
                self.lane.add_vehicle(self)
            else:
                # Exited the road network
                self._position = self.lane.length
                self.lane.remove_vehicle(self)
                self._state = VehicleState.EXITED
                self._speed = 0.0
                self._acceleration = 0.0
                break
