from typing import Any


def get_system_prompt(history_log: str = "") -> str:
    return f"""You are an experienced auto-rickshaw driver in Bengaluru, India. You have been driving autos for many years and know the city well.

Your goal is to maximize your earnings over 30 days while managing your 12-hour shift each day.

KEY RULES:
- You start each day at Majestic (the central bus/rail station)
- You have a 12-hour shift limit per day
- You must return your auto to Majestic at the end of each shift (even if far away - this costs fuel)
- Your bank balance tracks your total earnings

FARE STRUCTURE:
- Day (05:00 to 22:00): ₹36 minimum (up to 2 km) + ₹18/km for remaining distance
- Night (22:01 to 04:59): 1.5x multiplier! ₹54 minimum (up to 2 km) + ₹27/km
- Surge pricing applies during peak demand hours (morning IT rush, evening residential, etc.)
- Rainy days have higher fares (~30% more) but much worse traffic

FUEL COSTS (you must estimate these yourself):
- Petrol costs ₹100/litre. Your auto gets 25 km/litre while moving.
- Sitting idle in traffic burns 0.015 litres/minute extra.
- Heavy traffic means higher fuel costs due to idle burn, reducing your actual profit.
- Your profit = fare earned - fuel cost for that ride.

DECISIONS YOU CAN MAKE:
- Choose one of the ride options offered (e.g. 'A', 'B', 'C')
- "reject": Decline all rides and wait for next offers (costs idle time!)
- "end_shift": Stop working for the day and return to Majestic

IMPORTANT TIPS:
- Rejecting rides costs idle wait time (varies by time of day AND your location)
- At major hubs (Majestic, Hebbal, KR Puram) waits are shorter; at remote areas they're longer
- Night rides (after 10 PM) pay 1.5x but pings are rare (long wait if you reject)
- Long rides in heavy traffic have high fuel costs - estimate your profit carefully
- Try to end your shift near Majestic to minimize deadhead (empty return) fuel cost
- Known traffic bottlenecks: Silk Board junction, Outer Ring Road, Hebbal flyover
- Position yourself at Transit hubs for more ride options

Your response must be JSON with two fields:
- "action": One of the ride option letters (e.g. "A", "B", "C"), "reject", or "end_shift"
- "reasoning": Brief explanation of your decision

{history_log}"""


def get_start_day_prompt(
    day: int,
    day_name: str,
    bank_balance: float,
    is_rainy: bool = False,
) -> str:
    rain_note = ""
    if is_rainy:
        rain_note = "\n🌧️ Heavy rain today! Traffic will be significantly worse but fares are higher (~30% more)."

    return f"""Day {day} ({day_name}). Location: Majestic. Bank Balance: ₹{bank_balance:.0f}.{rain_note}

What time do you want to start your shift today?

Respond in JSON: {{"start_time": "HH:MM", "reasoning": "..."}}"""


def get_multi_ride_prompt(
    current_time: str,
    current_location: str,
    rides: list,
    shift_remaining: str,
    is_rainy: bool = False,
) -> str:
    rain_tag = " 🌧️" if is_rainy else ""
    option_labels = ["A", "B", "C", "D", "E"]

    lines = [
        f"Time: {current_time}{rain_tag}. Location: {current_location}.",
        f"Shift remaining: {shift_remaining}.",
        "",
        f"You have {len(rides)} ride offer{'s' if len(rides) > 1 else ''}:",
        "",
    ]

    for i, ride in enumerate(rides):
        label = option_labels[i]
        lines.append(f"  Option {label}: {ride['origin']} → {ride['destination']}")
        lines.append(
            f"    Distance: {ride['distance_km']:.1f} km | "
            f"Fare: ₹{ride['fare']:.0f} | "
            f"ETA: {ride['eta_min']} mins"
        )
        lines.append("")

    valid_actions = ", ".join([f"'{option_labels[i]}'" for i in range(len(rides))])
    lines.append(f"Action: {valid_actions}, 'reject', or 'end_shift'.")
    lines.append('Respond in JSON: {"action": "...", "reasoning": "..."}')

    return "\n".join(lines)


def get_end_shift_prompt(
    current_time: str,
    current_location: str,
    shift_remaining: str,
    deadhead_cost: float,
) -> str:
    return f"""Time: {current_time}. Location: {current_location}.
Shift remaining: {shift_remaining}.
Deadhead cost to return to Majestic: ₹{deadhead_cost:.0f}.

The shift is over. You must end your shift and return to Majestic.

Respond in JSON: {{"action": "end_shift", "reasoning": "..."}}"""


def parse_llm_response(response: dict[str, Any]) -> tuple[str, str]:
    action = response.get("action", "reject")
    reasoning = response.get("reasoning", "No reasoning provided")
    return action, reasoning
