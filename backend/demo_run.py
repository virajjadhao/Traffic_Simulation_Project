from src.controllers.fixed_time_signal import FixedTimeSignalController
from src.core.enums import Direction
from src.metrics.definitions.throughput import calculate_throughput
from src.metrics.definitions.wait_time import calculate_average_wait_time
from src.roads.network import RoadNetwork
from src.vehicles.idm import IntelligentDriverModel
from src.vehicles.pool import VehiclePool
from src.vehicles.spawner import VehicleSpawner


def main() -> None:
    print("=" * 60)
    print("Traffic Simulation Framework: Live Tick Logger Demo")
    print("=" * 60)

    # 1. Initialize Network & Corridors
    network = RoadNetwork()
    network.setup_default_intersection(
        approach_length=150.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    print("[Setup] Symmetrical 4-way intersection built (150m legs).")

    # 2. Setup Spawner (spawns up to 10 vehicles)
    spawner = VehicleSpawner(
        network,
        arrival_rate=1.5,
        total_vehicles=40,
        random_seed=123,
    )
    print("[Setup] Spawner ready (arrival rate = 1.5 vehicles/sec).")

    # 3. Setup Physics Engine (IDM)
    idm = IntelligentDriverModel(
        max_acceleration=2.5,
        comfort_deceleration=3.0,
        desired_time_headway=1.5,
        minimum_gap=2.5,
    )
    print("[Setup] Intelligent Driver Model (IDM) physics loaded.")

    # 4. Setup Intersection Controller (Fixed-Time Signals)
    # Fast cycle timings just for the demo
    controller = FixedTimeSignalController(
        green_time=8.0,
        yellow_time=2.0,
        all_red_time=1.0,
    )
    print(
        f"[Setup] Fixed-Time Signal Controller loaded (Current: {controller.current_phase})."  # noqa: E501
    )

    # 5. Initialize Vehicle Pool
    # We start with signal state map
    signals = {
        Direction.NORTH: True,
        Direction.SOUTH: True,
        Direction.EAST: False,
        Direction.WEST: False,
    }
    pool = VehiclePool(spawner, idm, traffic_signals=signals)

    # 6. Execute Simulation Tick Loop
    dt = 0.1
    duration = 60.0  # run 60 seconds (600 ticks)
    total_ticks = int(duration / dt)

    print(
        f"\n[Run] Starting simulation for {duration} seconds ({total_ticks} ticks)..."
    )
    print("-" * 60)

    active_vehicle_ids = set()

    for tick in range(1, total_ticks + 1):
        elapsed_time = tick * dt

        # Update controller timers
        controller.update(dt, pool.active_vehicles)

        # Convert controller signal head array into direction lookup map
        signals_state = {}
        for head in controller.get_signals_state():
            dir_str = head["direction"]
            color = head["color"]
            # Map string name to Enum
            dir_enum = getattr(Direction, dir_str.upper())
            signals_state[dir_enum] = color == "green"

        # Set signal inputs for the vehicle leader detection
        pool.set_traffic_signals(signals_state)

        # Record vehicle list before update to catch spawn/exit transitions
        prev_active = set(v.vehicle_id for v in pool.active_vehicles)

        # Run physics update tick
        pool.update(dt, elapsed_time)

        # Log new spawns
        for v in pool.active_vehicles:
            if v.vehicle_id not in active_vehicle_ids:
                active_vehicle_ids.add(v.vehicle_id)
                # Determine its route directions
                route_lanes = v.route
                start_dir = route_lanes[0].lane_id.split("_")[0].upper()
                end_dir = route_lanes[-1].lane_id.split("_")[0].upper()
                print(
                    f"  |-- [SPAWN] Vehicle '{v.vehicle_id}' entered from {start_dir} heading to {end_dir}"  # noqa: E501
                )

        # Log exits
        current_active = set(v.vehicle_id for v in pool.active_vehicles)
        exited_this_tick = prev_active - current_active
        for v_id in exited_this_tick:
            # Find the vehicle in the exited pool
            for v in pool.exited_vehicles:
                if v.vehicle_id == v_id:
                    print(
                        f"  |-- [EXIT] Vehicle '{v.vehicle_id}' completed route. Wait Time: {v.wait_time:.2f}s, Stops: {v.stop_count}"  # noqa: E501
                    )

        # Print snapshot summary every 2.0 seconds (20 ticks)
        if tick % 20 == 0:
            avg_wait = calculate_average_wait_time(pool.exited_vehicles)
            _throughput = calculate_throughput(
                pool.exited_vehicles, elapsed_time, warmup_time=0.0
            )

            signal_summary = ", ".join(
                [f"{d.value[0].upper()}:{col}" for d, col in signals_state.items()]
            )

            print(
                f"Time: {elapsed_time:4.1f}s | Active: {pool.active_count:2d} | Exited: {pool.exited_count:2d} | "  # noqa: E501
                f"Avg Wait: {avg_wait['value']:4.2f}s | Phase: {controller.current_phase:<9} | Signals ({signal_summary})"  # noqa: E501
            )

    print("-" * 60)
    print("[Done] Simulation run complete.")
    print("=" * 60)
    print("Final Performance Metrics:")
    final_avg_wait = calculate_average_wait_time(pool.exited_vehicles)
    final_throughput = calculate_throughput(
        pool.exited_vehicles, duration, warmup_time=0.0
    )

    print(f" - Total Throughput: {final_throughput['value']} vehicles")
    print(f" - Flow Rate:         {final_throughput['rate']:.2f} vehicles/min")
    print(f" - Average Wait Time: {final_avg_wait['value']:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()
