from src.config import (
    DAY_FARE_MINIMUM,
    DAY_FARE_PER_KM,
    NIGHT_FARE_MINIMUM,
    NIGHT_FARE_PER_KM,
    NIGHT_START_HOUR,
    NIGHT_END_HOUR,
    SURGE_MULTIPLIERS,
    RAIN_FARE_MULTIPLIER,
)


def _get_time_slot(time: str, day_of_week: int) -> str:
    hour = int(time.split(":")[0])
    is_weekend = day_of_week >= 5

    if is_weekend:
        return "weekend"
    else:
        if 6 <= hour < 10:
            return "weekday_morning"
        elif 10 <= hour < 16:
            return "weekday_midday"
        elif 16 <= hour < 22:
            return "weekday_evening"
        else:
            return "weekday_night"


def get_surge_multiplier(
    time: str, day_of_week: int, destination_type: str
) -> float:
    slot = _get_time_slot(time, day_of_week)
    return SURGE_MULTIPLIERS.get(slot, {}).get(destination_type, 1.0)


def calculate_fare(
    distance_km: float,
    time: str,
    day_of_week: int = 0,
    destination_type: str = "Transit",
    is_rainy: bool = False,
) -> float:
    hour = int(time.split(":")[0])
    minute = int(time.split(":")[1])
    total_minutes = hour * 60 + minute

    night_start = NIGHT_START_HOUR * 60 + 1
    night_end = NIGHT_END_HOUR * 60
    is_night = total_minutes >= night_start or total_minutes < night_end

    if is_night:
        minimum_fare = NIGHT_FARE_MINIMUM
        per_km_rate = NIGHT_FARE_PER_KM
    else:
        minimum_fare = DAY_FARE_MINIMUM
        per_km_rate = DAY_FARE_PER_KM

    if distance_km <= 2:
        base_fare = minimum_fare
    else:
        base_fare = minimum_fare + (distance_km - 2) * per_km_rate

    surge = get_surge_multiplier(time, day_of_week, destination_type)
    fare = base_fare * surge

    if is_rainy:
        fare *= RAIN_FARE_MULTIPLIER

    return round(fare, 2)
