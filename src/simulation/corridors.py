SILK_BOARD_ZONE = {
    "Electronic City Phase 1",
    "Koramangala",
    "Brigade Tech Gardens",
    "EcoWorld Bellandur",
    "Jayanagar 4th block",
}

ORR_BELT = {
    "ITPL Bengaluru",
    "EcoWorld Bellandur",
    "Brigade Tech Gardens",
    "Manyata Tech Park",
}

HEBBAL_ZONE = {
    "Hebbal",
    "Manyata Tech Park",
    "Yelahnka",
    "Vidyaranyapura",
    "Sahakara Nagar",
}

CENTRAL_ZONE = {
    "Majestic",
    "Chickpet",
    "KR Market",
    "Commercial street",
    "Russel Market",
    "Gandhi Bazaar",
}


def get_corridor_bonus(
    origin: str, destination: str, time: str
) -> float:
    hour = int(time.split(":")[0])
    minute = int(time.split(":")[1])
    total_minutes = hour * 60 + minute

    bonus = 0.0

    is_morning_peak = 8 * 60 <= total_minutes < 10 * 60
    is_evening_peak = 17 * 60 <= total_minutes < 20 * 60
    is_peak = is_morning_peak or is_evening_peak

    if is_peak and (
        origin in SILK_BOARD_ZONE or destination in SILK_BOARD_ZONE
    ):
        bonus += 0.5
    if is_peak and (
        origin in ORR_BELT and destination in ORR_BELT
    ):
        bonus += 0.3
    if is_morning_peak and (
        origin in HEBBAL_ZONE or destination in HEBBAL_ZONE
    ):
        bonus += 0.4
    if origin in CENTRAL_ZONE and destination in CENTRAL_ZONE:
        bonus += 0.2

    return bonus
