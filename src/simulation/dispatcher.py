from pydantic import BaseModel
from typing import Optional, List
import random

from src.config import (
    DESTINATION_WEIGHTS,
    AUTO_RICKSHAW_SPEED_FACTOR,
    LOCATION_HUB_TIER,
    WAIT_TIER_MULTIPLIER,
)
from src.data.locations import get_locations_by_type, get_all_types
from src.data.routes import get_route
from src.simulation.traffic import get_traffic_multiplier, get_simulated_duration
from src.simulation.fares import calculate_fare
from src.simulation.fuel import calculate_fuel


class RideRequest(BaseModel):
    origin: str
    destination: str
    distance_km: float
    base_duration_min: float
    traffic_multiplier: float
    simulated_duration_min: float
    expected_fare: float
    fuel_cost: float


def get_idle_wait_minutes(time: str, location: str = "Majestic") -> int:
    hour = int(time.split(":")[0])
    total_minutes = hour * 60

    if 5 * 60 <= total_minutes < 10 * 60:
        base_wait = 10
    elif 10 * 60 <= total_minutes < 16 * 60:
        base_wait = 30
    elif 16 * 60 <= total_minutes < 22 * 60:
        base_wait = 15
    else:
        base_wait = 45

    tier = LOCATION_HUB_TIER.get(location, 2)
    multiplier = WAIT_TIER_MULTIPLIER[tier]
    return max(5, int(base_wait * multiplier))


def get_destination_type_weights(time: str, day_of_week: int) -> dict[str, float]:
    hour = int(time.split(":")[0])
    is_weekend = day_of_week >= 5

    if is_weekend:
        return DESTINATION_WEIGHTS["weekend"].copy()
    else:
        if 6 <= hour < 10:
            return DESTINATION_WEIGHTS["weekday_morning"].copy()
        elif 10 <= hour < 16:
            return DESTINATION_WEIGHTS["weekday_midday"].copy()
        elif 16 <= hour < 22:
            return DESTINATION_WEIGHTS["weekday_evening"].copy()
        else:
            return DESTINATION_WEIGHTS["weekday_night"].copy()


def select_destination_type(weights: dict[str, float], rng: random.Random) -> str:
    types = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(types, weights=probs, k=1)[0]


def _build_ride_request(
    current_location: str,
    dest_name: str,
    dest_type: str,
    current_time: str,
    day_of_week: int,
    is_rainy: bool,
    rng: random.Random,
) -> Optional[RideRequest]:
    try:
        route = get_route(current_location, dest_name)
    except KeyError:
        return None

    distance_km = route["distance_km"]
    osrm_duration_min = route["duration_min"]

    base_duration_min = osrm_duration_min * AUTO_RICKSHAW_SPEED_FACTOR

    traffic_multiplier = get_traffic_multiplier(
        current_time,
        day_of_week,
        dest_type,
        origin=current_location,
        destination=dest_name,
        is_rainy=is_rainy,
        rng=rng,
    )
    simulated_duration = get_simulated_duration(base_duration_min, traffic_multiplier)

    expected_fare = calculate_fare(
        distance_km, current_time, day_of_week, dest_type, is_rainy
    )
    fuel_cost = calculate_fuel(distance_km, base_duration_min, simulated_duration)

    return RideRequest(
        origin=current_location,
        destination=dest_name,
        distance_km=distance_km,
        base_duration_min=base_duration_min,
        traffic_multiplier=traffic_multiplier,
        simulated_duration_min=simulated_duration,
        expected_fare=expected_fare,
        fuel_cost=fuel_cost,
    )


def generate_ping(
    current_time: str,
    day_of_week: int,
    current_location: str,
    rng: random.Random | None = None,
    is_rainy: bool = False,
) -> Optional[RideRequest]:
    if rng is None:
        rng = random.Random()

    weights = get_destination_type_weights(current_time, day_of_week)
    destination_type = select_destination_type(weights, rng)
    destinations = get_locations_by_type(destination_type)

    if not destinations:
        all_locations = []
        for loc_type in get_all_types():
            all_locations.extend(get_locations_by_type(loc_type))
        destinations = all_locations

    available_destinations = [d for d in destinations if d.name != current_location]

    if not available_destinations:
        return None

    dest = rng.choice(available_destinations)

    return _build_ride_request(
        current_location, dest.name, dest.type,
        current_time, day_of_week, is_rainy, rng,
    )


def generate_multiple_pings(
    current_time: str,
    day_of_week: int,
    current_location: str,
    count: int = 3,
    rng: random.Random | None = None,
    is_rainy: bool = False,
) -> List[RideRequest]:
    if rng is None:
        rng = random.Random()

    rides: List[RideRequest] = []
    seen_destinations: set[str] = set()
    attempts = 0
    max_attempts = count * 4

    while len(rides) < count and attempts < max_attempts:
        attempts += 1

        weights = get_destination_type_weights(current_time, day_of_week)
        destination_type = select_destination_type(weights, rng)
        destinations = get_locations_by_type(destination_type)

        if not destinations:
            all_locations = []
            for loc_type in get_all_types():
                all_locations.extend(get_locations_by_type(loc_type))
            destinations = all_locations

        available = [
            d for d in destinations
            if d.name != current_location and d.name not in seen_destinations
        ]

        if not available:
            continue

        dest = rng.choice(available)
        ride = _build_ride_request(
            current_location, dest.name, dest.type,
            current_time, day_of_week, is_rainy, rng,
        )

        if ride is not None:
            rides.append(ride)
            seen_destinations.add(dest.name)

    return rides
