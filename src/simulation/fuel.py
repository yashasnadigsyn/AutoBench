from src.config import FUEL_PRICE_PER_LITER, KM_PER_LITER, IDLE_BURN_PER_MINUTE


def calculate_fuel(
    distance_km: float, base_duration_min: float, simulated_duration_min: float
) -> float:
    delay_minutes = simulated_duration_min - base_duration_min
    if delay_minutes < 0:
        delay_minutes = 0

    total_liters = (distance_km / KM_PER_LITER) + (delay_minutes * IDLE_BURN_PER_MINUTE)
    fuel_cost = total_liters * FUEL_PRICE_PER_LITER

    return round(fuel_cost, 2)
