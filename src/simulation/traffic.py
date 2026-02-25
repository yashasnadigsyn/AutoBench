import random
from typing import Literal, Optional

from src.simulation.corridors import get_corridor_bonus

LocationType = Literal["IT", "Markets", "Residential", "Transit"]


def _get_base_multiplier(
    time: str, day_of_week: int, destination_type: LocationType
) -> float:
    hour = int(time.split(":")[0])
    minute = int(time.split(":")[1])
    total_minutes = hour * 60 + minute

    is_weekend = day_of_week >= 5

    if not is_weekend:
        if 7 * 60 <= total_minutes < 10 * 60:
            if destination_type == "IT":
                return 3.5
            elif destination_type == "Transit":
                return 2.0
            else:
                return 1.5
        elif 10 * 60 <= total_minutes < 16 * 60:
            if destination_type == "Markets":
                return 2.5
            elif destination_type == "IT":
                return 1.5
            else:
                return 1.5
        elif 16 * 60 <= total_minutes < 22 * 60:
            if destination_type == "Residential":
                return 3.0
            elif destination_type == "Transit":
                return 2.5
            else:
                return 1.8
        else:
            return 1.0
    else:
        if 6 * 60 <= total_minutes < 10 * 60:
            return 1.2
        elif 10 * 60 <= total_minutes < 22 * 60:
            if destination_type == "IT":
                return 1.2
            else:
                return 2.2
        elif 22 * 60 <= total_minutes or total_minutes < 6 * 60:
            return 1.0
        else:
            return 1.0


def get_traffic_multiplier(
    time: str,
    day_of_week: int,
    destination_type: LocationType,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    is_rainy: bool = False,
    rng: Optional[random.Random] = None,
) -> float:
    from src.config import RAIN_TRAFFIC_MULTIPLIER

    base = _get_base_multiplier(time, day_of_week, destination_type)

    corridor_bonus = 0.0
    if origin and destination:
        corridor_bonus = get_corridor_bonus(origin, destination, time)

    multiplier = base + corridor_bonus

    if rng is not None:
        noise = rng.uniform(0.8, 1.2)
        multiplier *= noise

    if is_rainy:
        multiplier *= RAIN_TRAFFIC_MULTIPLIER

    return max(1.0, multiplier)


def get_simulated_duration(base_duration_min: float, multiplier: float) -> float:
    return base_duration_min * multiplier
