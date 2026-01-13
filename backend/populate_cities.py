#!/usr/bin/env python3
"""
Script to populate the cities table with coordinates using Nominatim (OpenStreetMap) geocoding.
Free service with rate limiting (1 request per second).
"""
import time
import requests
from app import app, db
from models import City
from constants import BOSNIAN_CITIES

# Nominatim API endpoint (free, no API key required)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Headers required by Nominatim (they require a valid User-Agent)
HEADERS = {
    "User-Agent": "PopustBA/1.0 (https://popust.ba; contact@popust.ba)"
}

def geocode_city(city_name: str, country: str = "Bosnia and Herzegovina") -> dict:
    """
    Get latitude and longitude for a city using Nominatim API.
    Returns dict with 'lat' and 'lon' or None if not found.
    """
    params = {
        "q": f"{city_name}, {country}",
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data and len(data) > 0:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "display_name": data[0].get("display_name", "")
            }
        return None
    except Exception as e:
        print(f"  Error geocoding {city_name}: {e}")
        return None


def populate_cities():
    """Populate the cities table with all Bosnian cities and their coordinates."""
    with app.app_context():
        # Create the cities table if it doesn't exist
        db.create_all()

        print(f"Starting to populate {len(BOSNIAN_CITIES)} cities...")
        print("Using Nominatim API (1 request per second rate limit)\n")

        success_count = 0
        failed_cities = []

        for i, city_name in enumerate(BOSNIAN_CITIES, 1):
            # Check if city already exists
            existing = City.query.filter_by(name=city_name).first()
            if existing:
                if existing.latitude and existing.longitude:
                    print(f"[{i}/{len(BOSNIAN_CITIES)}] {city_name} - Already exists with coordinates")
                    success_count += 1
                    continue
                else:
                    # City exists but no coordinates, update it
                    city = existing
            else:
                # Create new city
                city = City(name=city_name)
                db.session.add(city)

            # Geocode the city
            print(f"[{i}/{len(BOSNIAN_CITIES)}] Geocoding {city_name}...", end=" ")
            result = geocode_city(city_name)

            if result:
                city.latitude = result["lat"]
                city.longitude = result["lon"]
                db.session.commit()
                print(f"✓ ({result['lat']:.4f}, {result['lon']:.4f})")
                success_count += 1
            else:
                # Try with just city name (without country)
                result = geocode_city(city_name, "")
                if result:
                    city.latitude = result["lat"]
                    city.longitude = result["lon"]
                    db.session.commit()
                    print(f"✓ ({result['lat']:.4f}, {result['lon']:.4f}) [fallback]")
                    success_count += 1
                else:
                    db.session.commit()  # Save city without coordinates
                    print("✗ Not found")
                    failed_cities.append(city_name)

            # Rate limiting: 1 request per second (Nominatim requirement)
            time.sleep(1.1)

        print(f"\n{'='*50}")
        print(f"Completed! {success_count}/{len(BOSNIAN_CITIES)} cities geocoded successfully")

        if failed_cities:
            print(f"\nFailed to geocode ({len(failed_cities)}):")
            for city in failed_cities:
                print(f"  - {city}")

        # Show summary
        total_cities = City.query.count()
        cities_with_coords = City.query.filter(City.latitude.isnot(None)).count()
        print(f"\nDatabase summary:")
        print(f"  Total cities: {total_cities}")
        print(f"  With coordinates: {cities_with_coords}")
        print(f"  Missing coordinates: {total_cities - cities_with_coords}")

        # Update users' city_id from their city string
        update_users_city_id()


def update_users_city_id():
    """Update users' city_id from their existing city string."""
    from models import User
    from sqlalchemy import text

    print("\n" + "="*50)
    print("Updating users' city_id from city strings...")

    # Get users with city string but no city_id
    result = db.session.execute(text("""
        UPDATE users u
        SET city_id = c.id
        FROM cities c
        WHERE u.city = c.name
        AND u.city IS NOT NULL
        AND u.city_id IS NULL
    """))
    db.session.commit()

    updated_count = result.rowcount
    print(f"  Updated {updated_count} users with city_id")

    # Check for users with city string that doesn't match any city
    orphaned = db.session.execute(text("""
        SELECT DISTINCT city FROM users
        WHERE city IS NOT NULL
        AND city_id IS NULL
    """)).fetchall()

    if orphaned:
        print(f"\n  Warning: {len(orphaned)} city values don't match any city in the database:")
        for row in orphaned:
            print(f"    - {row[0]}")


def add_missing_coordinates():
    """Try to add coordinates to cities that are missing them."""
    with app.app_context():
        missing = City.query.filter(City.latitude.is_(None)).all()

        if not missing:
            print("All cities have coordinates!")
            return

        print(f"Found {len(missing)} cities without coordinates. Geocoding...\n")

        for city in missing:
            print(f"Geocoding {city.name}...", end=" ")
            result = geocode_city(city.name)

            if result:
                city.latitude = result["lat"]
                city.longitude = result["lon"]
                db.session.commit()
                print(f"✓ ({result['lat']:.4f}, {result['lon']:.4f})")
            else:
                print("✗ Not found")

            time.sleep(1.1)


def list_cities():
    """List all cities in the database with their coordinates."""
    with app.app_context():
        cities = City.query.order_by(City.name).all()

        print(f"\nTotal cities: {len(cities)}\n")
        print(f"{'Name':<30} {'Latitude':>12} {'Longitude':>12}")
        print("-" * 56)

        for city in cities:
            lat = f"{city.latitude:.4f}" if city.latitude else "N/A"
            lon = f"{city.longitude:.4f}" if city.longitude else "N/A"
            print(f"{city.name:<30} {lat:>12} {lon:>12}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_cities()
        elif sys.argv[1] == "missing":
            add_missing_coordinates()
        elif sys.argv[1] == "update-users":
            with app.app_context():
                update_users_city_id()
        else:
            print("Usage: python populate_cities.py [list|missing|update-users]")
            print("  (no args)    - Populate all cities + update users")
            print("  list         - List all cities in database")
            print("  missing      - Only geocode cities missing coordinates")
            print("  update-users - Update users' city_id from city strings")
    else:
        populate_cities()
