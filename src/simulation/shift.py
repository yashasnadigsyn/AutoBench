import random
from typing import Optional

from src.config import AUTO_RICKSHAW_SPEED_FACTOR
from src.data.routes import get_route
from src.simulation.fuel import calculate_fuel
from src.simulation.traffic import get_traffic_multiplier, get_simulated_duration


def parse_time(time_str: str) -> int:
    hour = int(time_str.split(":")[0])
    minute = int(time_str.split(":")[1])
    return hour * 60 + minute


def time_to_str(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def add_minutes(time_str: str, minutes: int) -> str:
    total = parse_time(time_str) + minutes
    total = total % (24 * 60)
    if total < 0:
        total = 0
    return time_to_str(total)


def ride_fits_in_shift(
    current_time: str, ride_duration_min: int, shift_remaining_min: int
) -> bool:
    return ride_duration_min <= shift_remaining_min


def calculate_deadhead(
    origin: str,
    destination: str,
    time: str,
    day_of_week: int,
    is_rainy: bool = False,
    rng: Optional[random.Random] = None,
) -> float:
    route = get_route(origin, destination)
    distance_km = route["distance_km"]
    osrm_duration_min = route["duration_min"]

    base_duration_min = osrm_duration_min * AUTO_RICKSHAW_SPEED_FACTOR

    from src.data.locations import get_location_by_name

    dest_location = get_location_by_name(destination)
    dest_type = dest_location.type if dest_location else "Transit"

    traffic_multiplier = get_traffic_multiplier(
        time, day_of_week, dest_type,
        origin=origin, destination=destination,
        is_rainy=is_rainy, rng=rng,
    )
    simulated_duration = get_simulated_duration(base_duration_min, traffic_multiplier)

    fuel_cost = calculate_fuel(distance_km, base_duration_min, simulated_duration)
    return fuel_cost
