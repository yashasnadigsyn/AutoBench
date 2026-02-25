import json
from typing import Dict, Any

from src.config import BASE_ROUTES_PATH

_routes_cache: Dict[str, Dict[str, Any]] = {}


def load_routes() -> Dict[str, Dict[str, Any]]:
    global _routes_cache
    if _routes_cache:
        return _routes_cache

    try:
        with open(BASE_ROUTES_PATH, "r") as f:
            _routes_cache = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Routes file not found: {BASE_ROUTES_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in routes file: {e}")

    return _routes_cache


def get_route(origin: str, destination: str) -> Dict[str, float]:
    routes = load_routes()

    if origin not in routes:
        raise KeyError(f"Origin '{origin}' not found in routes")

    if destination not in routes[origin]:
        raise KeyError(f"Destination '{destination}' not found for origin '{origin}'")

    return routes[origin][destination]


def get_routes_from(origin: str) -> Dict[str, Dict[str, float]]:
    routes = load_routes()

    if origin not in routes:
        raise KeyError(f"Origin '{origin}' not found in routes")

    return routes[origin]


def get_all_origin_names() -> list:
    routes = load_routes()
    return list(routes.keys())


def has_route(origin: str, destination: str) -> bool:
    try:
        get_route(origin, destination)
        return True
    except KeyError:
        return False
