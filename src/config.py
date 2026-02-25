from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

CSV_PATH = PROJECT_ROOT / "locations.csv"
BASE_ROUTES_PATH = PROJECT_ROOT / "base_routes.json"

FUEL_PRICE_PER_LITER = 100
KM_PER_LITER = 25
IDLE_BURN_PER_MINUTE = 0.015
AUTO_RICKSHAW_SPEED_FACTOR = 1.5

SHIFT_DURATION_MINUTES = 12 * 60

DAY_FARE_MINIMUM = 36
DAY_FARE_PER_KM = 18
NIGHT_FARE_MINIMUM = 54
NIGHT_FARE_PER_KM = 27
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 5

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

LOCATION_TYPES = ["IT", "Markets", "Residential", "Transit"]

DESTINATION_WEIGHTS = {
    "weekday_morning": {
        "IT": 0.7,
        "Transit": 0.15,
        "Markets": 0.15,
        "Residential": 0.0,
    },
    "weekday_midday": {
        "Markets": 0.6,
        "IT": 0.133,
        "Transit": 0.133,
        "Residential": 0.134,
    },
    "weekday_evening": {
        "Residential": 0.7,
        "Transit": 0.15,
        "Markets": 0.15,
        "IT": 0.0,
    },
    "weekday_night": {
        "Transit": 0.8,
        "Residential": 0.2,
        "Markets": 0.0,
        "IT": 0.0,
    },
    "weekend": {
        "Markets": 0.4,
        "Transit": 0.3,
        "Residential": 0.3,
        "IT": 0.0,
    },
}

RAIN_PROBABILITY = 0.20
RAIN_TRAFFIC_MULTIPLIER = 1.5
RAIN_FARE_MULTIPLIER = 1.3

SURGE_MULTIPLIERS = {
    "weekday_morning": {"IT": 1.4, "Transit": 1.2, "Markets": 1.0, "Residential": 1.0},
    "weekday_midday": {"Markets": 1.3, "IT": 1.0, "Transit": 1.0, "Residential": 1.0},
    "weekday_evening": {"Residential": 1.3, "Transit": 1.2, "Markets": 1.0, "IT": 1.0},
    "weekday_night": {"Transit": 1.2, "Residential": 1.0, "Markets": 1.0, "IT": 1.0},
    "weekend": {"Markets": 1.3, "Transit": 1.1, "Residential": 1.1, "IT": 1.0},
}

LOCATION_HUB_TIER = {
    "Majestic": 1,
    "KR Puram": 1,
    "Hebbal": 1,
    "Yeshwanthpur Railway Station": 1,
    "Kengeri Satellite Bus Stand": 1,
    "Goraguntepalya": 1,
    "Electronic City Phase 1": 2,
    "Manyata Tech Park": 2,
    "ITPL Bengaluru": 2,
    "Koramangala": 2,
    "Chickpet": 2,
    "KR Market": 2,
    "Commercial street": 2,
    "Indiranagar": 2,
    "Malleshwaram 8th cross": 2,
    "Gandhi Bazaar": 2,
    "Jayanagar 4th block": 2,
    "RT Nagar": 2,
    "Lalbagh": 2,
    "Russel Market": 2,
    "Peenya Industrial Area": 2,
    "Chandra Layout": 2,
    "Hoskote": 3,
    "Jigani Industrial Area": 3,
    "Bannerghatta Zoo": 3,
    "Yelahnka": 3,
    "Vidyaranyapura": 3,
    "Yalachenahalli": 3,
    "Sahakara Nagar": 3,
    "Laggere": 3,
    "Mathikere": 3,
    "EcoWorld Bellandur": 3,
    "Brigade Tech Gardens": 3,
}

WAIT_TIER_MULTIPLIER = {1: 0.5, 2: 1.0, 3: 1.8}

API_BASE_URL = "https://api.synthetic.new/openai/v1"
API_QUOTA_URL = "https://api.synthetic.new/v2/quotas"
DEFAULT_MODEL = "hf:openai/gpt-oss-120b"
DEFAULT_DAYS = 7
DEFAULT_OUTPUT_DIR = "results"
