import csv
import json
import time
import requests
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "locations.csv"
OUTPUT_PATH = Path(__file__).parent.parent / "base_routes.json"
FAILED_PATH = Path(__file__).parent.parent / "failed.txt"

BASE_URL = "http://router.project-osrm.org/route/v1/driving"


def load_locations():
    locations = []
    try:
        with open(CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(
                    {
                        "type": row["type"].strip(),
                        "name": row["location"].strip(),
                        "lat": float(row["lat"].strip()),
                        "lon": float(row["lon"].strip()),
                    }
                )
    except Exception as e:
        print(f"Error loading locations: {e}")
        raise
    return locations


def load_existing_routes():
    try:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading existing routes: {e}")
    return {}


def load_failed_routes():
    failed = []
    try:
        if FAILED_PATH.exists():
            with open(FAILED_PATH, "r") as f:
                for line in f:
                    failed.append(line.strip())
    except Exception as e:
        print(f"Error loading failed routes: {e}")
    return failed


def save_routes(routes):
    try:
        with open(OUTPUT_PATH, "w") as f:
            json.dump(routes, f, indent=2)
    except Exception as e:
        print(f"Error saving routes: {e}")


def save_failed_routes(failed_routes):
    try:
        with open(FAILED_PATH, "w") as f:
            for pair in failed_routes:
                f.write(pair + "\n")
    except Exception as e:
        print(f"Error saving failed routes: {e}")


def fetch_route(lon1, lat1, lon2, lat2, retries=3):
    url = f"{BASE_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                print("Rate limited, waiting 60 seconds...")
                time.sleep(60)
                continue

            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                return None

            route = data["routes"][0]
            distance_km = route["distance"] / 1000
            duration_min = route["duration"] / 60

            return {
                "distance_km": round(distance_km, 2),
                "duration_min": round(duration_min, 1),
            }

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"Failed after {retries} attempts: {e}")
                return None

    return None


def main():
    print("Loading locations...")
    locations = load_locations()
    print(f"Loaded {len(locations)} locations")

    print("Loading existing routes...")
    routes = load_existing_routes()
    existing_count = sum(len(v) for v in routes.values())
    print(f"Loaded {len(routes)} origins with {existing_count} routes")

    print("Loading existing failed routes...")
    failed_routes = load_failed_routes()
    print(f"Loaded {len(failed_routes)} previously failed routes")

    total_pairs = len(locations) * (len(locations) - 1)
    processed = existing_count + len(failed_routes)

    print(f"Fetching remaining {total_pairs - processed} route pairs...")

    for origin in locations:
        origin_name = origin["name"]

        if origin_name in routes:
            print(f"Skipping origin '{origin_name}' (already fetched)")
            continue

        routes[origin_name] = {}

        for destination in locations:
            if origin_name == destination["name"]:
                continue

            dest_name = destination["name"]
            pair_key = f"{origin_name} -> {dest_name}"

            if pair_key in failed_routes:
                continue

            processed += 1

            result = fetch_route(
                origin["lon"], origin["lat"], destination["lon"], destination["lat"]
            )

            if result:
                routes[origin_name][dest_name] = result
            else:
                failed_routes.append(pair_key)
                print(f"Warning: No route found for {pair_key}")

            if processed % 50 == 0:
                print(f"Processed {processed}/{total_pairs} pairs, saving progress...")
                save_routes(routes)
                save_failed_routes(failed_routes)

            time.sleep(1)

    print(f"\nSaving final routes to {OUTPUT_PATH}...")
    save_routes(routes)

    if failed_routes:
        print(f"Saving {len(failed_routes)} failed routes to {FAILED_PATH}...")
        save_failed_routes(failed_routes)

    print(
        f"\nDone! Successfully fetched {sum(len(v) for v in routes.values())} routes."
    )
    print(f"Failed routes: {len(failed_routes)}")


if __name__ == "__main__":
    main()
