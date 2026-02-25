from typing import List
from src.simulation.state import RideEvent, DAY_NAMES


def compress_history(
    day: int,
    day_of_week: int,
    shift_start: str,
    shift_end: str,
    ended_location: str,
    rides: List[RideEvent],
    today_gross: float,
    today_fuel: float,
    today_deadhead: float,
    total_bank_balance: float,
    is_rainy: bool = False,
) -> str:
    net_profit = today_gross - today_fuel - today_deadhead

    notes = []
    if is_rainy:
        notes.append("Rainy day — higher fares but worse traffic.")
    if ended_location != "Majestic":
        notes.append(
            "You ended far from Majestic, causing a high deadhead penalty. "
            "Try taking your final rides toward Transit nodes."
        )

    note_str = " ".join(notes)
    if note_str:
        note_str = f" Note: {note_str}"

    rain_tag = " 🌧️" if is_rainy else ""

    return f"""=== HISTORY LOG ===
Day {day} ({DAY_NAMES[day_of_week]}{rain_tag}): Shift {shift_start} to {shift_end}.
Ended at: {ended_location}.
Rides: {len(rides)}. Gross: ₹{today_gross:.0f}.
Fuel (Rides): ₹{today_fuel:.0f}. Deadhead Fuel ({ended_location} to Majestic): ₹{today_deadhead:.0f}.
Net Profit Day {day}: ₹{net_profit:.0f}. Total Bank Balance: ₹{total_bank_balance:.0f}.{note_str}
=================="""

