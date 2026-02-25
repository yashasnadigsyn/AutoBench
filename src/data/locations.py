import csv
from typing import List, Optional
from pydantic import BaseModel

from src.config import CSV_PATH, LOCATION_TYPES

_locations_cache: List["Location"] | None = None


class Location(BaseModel):
    type: str
    name: str
    lat: float
    lon: float


def load_locations() -> List[Location]:
    global _locations_cache
    if _locations_cache is not None:
        return _locations_cache

    locations = []
    try:
        with open(CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(
                    Location(
                        type=row["type"].strip(),
                        name=row["location"].strip(),
                        lat=float(row["lat"].strip()),
                        lon=float(row["lon"].strip()),
                    )
                )
    except FileNotFoundError:
        raise FileNotFoundError(f"Locations file not found: {CSV_PATH}")
    except Exception as e:
        raise RuntimeError(f"Error loading locations: {e}")

    if len(locations) != 33:
        raise ValueError(f"Expected 33 locations, got {len(locations)}")

    _locations_cache = locations
    return _locations_cache


def get_location_by_name(name: str) -> Optional[Location]:
    locations = load_locations()
    for loc in locations:
        if loc.name == name:
            return loc
    return None


def get_locations_by_type(location_type: str) -> List[Location]:
    locations = load_locations()
    return [loc for loc in locations if loc.type == location_type]


def get_all_types() -> List[str]:
    return LOCATION_TYPES.copy()

