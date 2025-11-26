#!/usr/bin/env python3
"""
Script to retroactively populate google_link for all businesses
using their name and the default city (Tuzla) coordinates.
"""
from app import app, db
from models import Business, City


def populate_google_links(force_update: bool = False):
    """
    Populate google_link for all businesses that don't have one.

    Args:
        force_update: If True, update ALL businesses even if they have a google_link
    """
    with app.app_context():
        # Get all businesses
        if force_update:
            businesses = Business.query.all()
            print(f"Force updating google_link for all {len(businesses)} businesses...")
        else:
            businesses = Business.query.filter(
                (Business.google_link.is_(None)) | (Business.google_link == '')
            ).all()
            print(f"Found {len(businesses)} businesses without google_link...")

        if not businesses:
            print("No businesses to update!")
            return

        # Get default city coordinates (Tuzla as fallback)
        default_city = City.query.filter_by(name='Tuzla').first()
        if not default_city:
            print("Warning: Default city 'Tuzla' not found in database!")
            default_lat, default_lon = 44.5391, 18.6752  # Tuzla coordinates
        else:
            default_lat, default_lon = default_city.latitude, default_city.longitude

        updated_count = 0
        for business in businesses:
            # Try to get city coordinates for the business's city
            city = City.query.filter_by(name=business.city).first() if business.city else None

            if city and city.latitude and city.longitude:
                lat, lon = city.latitude, city.longitude
            else:
                lat, lon = default_lat, default_lon
                if business.city:
                    print(f"  Warning: City '{business.city}' not found, using default coordinates")

            # Generate the Google Maps link
            google_link = Business.generate_google_maps_link(business.name, lat, lon)

            # Update business
            business.google_link = google_link
            updated_count += 1
            print(f"  [{updated_count}] {business.name} ({business.city or 'No city'}) -> {google_link[:60]}...")

        # Commit all changes
        db.session.commit()
        print(f"\n✓ Successfully updated {updated_count} businesses with google_link")


def list_businesses():
    """List all businesses with their google_link."""
    with app.app_context():
        businesses = Business.query.order_by(Business.name).all()

        print(f"\nTotal businesses: {len(businesses)}\n")
        print(f"{'ID':<4} {'Name':<30} {'City':<15} {'Google Link':<50}")
        print("-" * 100)

        for b in businesses:
            link = (b.google_link[:47] + '...') if b.google_link and len(b.google_link) > 50 else (b.google_link or 'N/A')
            print(f"{b.id:<4} {b.name[:28]:<30} {(b.city or 'N/A')[:13]:<15} {link}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_businesses()
        elif sys.argv[1] == "force":
            populate_google_links(force_update=True)
        else:
            print("Usage: python populate_google_links.py [list|force]")
            print("  (no args) - Populate google_link for businesses missing it")
            print("  list      - List all businesses with their google_link")
            print("  force     - Force update ALL businesses (overwrites existing)")
    else:
        populate_google_links()
