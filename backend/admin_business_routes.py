"""
Admin API routes for managing business memberships
Uses JWT authentication (not flask_login session)
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
import requests
from datetime import datetime

admin_business_bp = Blueprint('admin_business', __name__, url_prefix='/api/admin/businesses')

logger = logging.getLogger(__name__)


def jwt_admin_required(f):
    """Decorator to require admin privileges via JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token
        from models import User

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401

            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403

            request.jwt_user = user
            request.jwt_user_id = user_id

        except Exception as e:
            logger.error(f"JWT auth error: {e}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)
    return decorated_function


@admin_business_bp.route('', methods=['GET'])
@jwt_admin_required
def get_all_businesses():
    """
    Get all businesses for admin management
    Query params:
    - search: optional search term for business name
    - page: page number (default 1)
    - per_page: items per page (default 50)
    """
    from models import Business

    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Business.query

    if search:
        query = query.filter(Business.name.ilike(f'%{search}%'))

    query = query.order_by(Business.name.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    businesses = [{
        'id': b.id,
        'name': b.name,
        'slug': b.slug,
        'city': b.city,
        'status': b.status,
        'logo_path': b.logo_path,
        'member_count': len(b.memberships) if b.memberships else 0
    } for b in pagination.items]

    return jsonify({
        'businesses': businesses,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@admin_business_bp.route('/<int:business_id>/members', methods=['GET'])
@jwt_admin_required
def get_business_members(business_id):
    """
    Get all members of a business
    """
    from models import Business, BusinessMembership

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    memberships = BusinessMembership.query.filter_by(
        business_id=business_id,
        is_active=True
    ).all()

    members = [{
        'id': m.id,
        'user_id': m.user_id,
        'email': m.user.email if m.user else None,
        'name': f"{m.user.first_name or ''} {m.user.last_name or ''}".strip() if m.user else None,
        'role': m.role,
        'is_active': m.is_active,
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in memberships]

    return jsonify({
        'business': {
            'id': business.id,
            'name': business.name
        },
        'members': members
    })


@admin_business_bp.route('/<int:business_id>/members', methods=['POST'])
@jwt_admin_required
def add_business_member(business_id):
    """
    Add a user to a business by email
    Body:
    - email: user's email address (required)
    - role: 'staff', 'manager', or 'owner' (default: 'staff')
    """
    from models import db, Business, User, BusinessMembership

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    email = data.get('email', '').strip().lower()
    role = data.get('role', 'staff')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    if role not in ['staff', 'manager', 'owner']:
        return jsonify({'error': 'Invalid role. Must be staff, manager, or owner'}), 400

    # Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': f'User with email {email} not found. User must register first.'}), 404

    # Check if user already has an active membership with ANY other business
    other_membership = BusinessMembership.query.filter(
        BusinessMembership.user_id == user.id,
        BusinessMembership.business_id != business_id,
        BusinessMembership.is_active == True
    ).first()

    if other_membership:
        other_business_name = other_membership.business.name if other_membership.business else 'another business'
        return jsonify({
            'error': f'User {email} is already a member of "{other_business_name}". A user can only belong to one business.'
        }), 400

    # Check if already a member of this business
    existing = BusinessMembership.query.filter_by(
        business_id=business_id,
        user_id=user.id
    ).first()

    if existing:
        if existing.is_active:
            return jsonify({'error': 'User is already a member of this business'}), 400
        else:
            # Reactivate membership
            existing.is_active = True
            existing.role = role
            existing.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"Reactivated membership for user {user.email} in business {business.name}")

            return jsonify({
                'success': True,
                'message': f'User {user.email} reactivated as {role} in {business.name}',
                'membership': {
                    'id': existing.id,
                    'user_id': user.id,
                    'email': user.email,
                    'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    'role': role
                }
            })

    # Create new membership
    membership = BusinessMembership(
        business_id=business_id,
        user_id=user.id,
        role=role,
        is_active=True
    )

    db.session.add(membership)
    db.session.commit()

    logger.info(f"Added user {user.email} as {role} to business {business.name}")

    return jsonify({
        'success': True,
        'message': f'User {user.email} added as {role} to {business.name}',
        'membership': {
            'id': membership.id,
            'user_id': user.id,
            'email': user.email,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'role': role
        }
    })


@admin_business_bp.route('/<int:business_id>/members/<membership_id>', methods=['PUT'])
@jwt_admin_required
def update_business_member(business_id, membership_id):
    """
    Update a member's role
    Body:
    - role: 'staff', 'manager', or 'owner'
    """
    from models import db, BusinessMembership

    membership = BusinessMembership.query.filter_by(
        id=membership_id,
        business_id=business_id
    ).first()

    if not membership:
        return jsonify({'error': 'Membership not found'}), 404

    data = request.get_json()
    role = data.get('role')

    if role and role not in ['staff', 'manager', 'owner']:
        return jsonify({'error': 'Invalid role'}), 400

    if role:
        membership.role = role

    membership.updated_at = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Membership updated',
        'membership': {
            'id': membership.id,
            'role': membership.role
        }
    })


@admin_business_bp.route('/<int:business_id>/members/<membership_id>', methods=['DELETE'])
@jwt_admin_required
def remove_business_member(business_id, membership_id):
    """
    Remove a member from a business (soft delete - sets is_active to False)
    """
    from models import db, BusinessMembership

    membership = BusinessMembership.query.filter_by(
        id=membership_id,
        business_id=business_id
    ).first()

    if not membership:
        return jsonify({'error': 'Membership not found'}), 404

    user_email = membership.user.email if membership.user else 'unknown'

    # Soft delete
    membership.is_active = False
    membership.updated_at = datetime.now()
    db.session.commit()

    logger.info(f"Removed user {user_email} from business {business_id}")

    return jsonify({
        'success': True,
        'message': f'User {user_email} removed from business'
    })


@admin_business_bp.route('/<int:business_id>', methods=['GET'])
@jwt_admin_required
def get_business(business_id):
    """
    Get a single business with all details
    """
    from models import Business

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    return jsonify({
        'business': {
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'city': business.city,
            'address': business.address,
            'contact_phone': business.contact_phone,
            'description': business.description,
            'working_hours': business.working_hours,
            'google_link': business.google_link,
            'logo_path': business.logo_path,
            'cover_image_path': business.cover_image_path,
            'status': business.status,
            'business_type': business.business_type
        }
    })


@admin_business_bp.route('/<int:business_id>', methods=['PUT'])
@jwt_admin_required
def update_business(business_id):
    """
    Update business details including slug
    Body can include:
    - slug: URL-friendly identifier (must be unique)
    - name, city, address, contact_phone, description, working_hours, google_link
    """
    from models import db, Business
    import re

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Handle slug update
    if 'slug' in data:
        new_slug = data['slug'].strip().lower() if data['slug'] else None

        if new_slug:
            # Validate slug format (only lowercase letters, numbers, and hyphens)
            if not re.match(r'^[a-z0-9-]+$', new_slug):
                return jsonify({'error': 'Slug can only contain lowercase letters, numbers, and hyphens'}), 400

            # Check if slug is already taken by another business
            existing = Business.query.filter(
                Business.slug == new_slug,
                Business.id != business_id
            ).first()
            if existing:
                return jsonify({'error': f'Slug "{new_slug}" is already in use by another business'}), 400

        business.slug = new_slug

    # Update other fields
    if 'name' in data:
        business.name = data['name']
    if 'city' in data:
        business.city = data['city']
    if 'address' in data:
        business.address = data['address']
    if 'contact_phone' in data:
        business.contact_phone = data['contact_phone']
    if 'description' in data:
        business.description = data['description']
    if 'working_hours' in data:
        business.working_hours = data['working_hours']
    if 'google_link' in data:
        business.google_link = data['google_link']
    if 'status' in data and data['status'] in ['active', 'inactive']:
        business.status = data['status']

    db.session.commit()

    logger.info(f"Updated business {business.id}: {business.name}")

    return jsonify({
        'success': True,
        'message': 'Business updated',
        'business': {
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'city': business.city,
            'address': business.address,
            'contact_phone': business.contact_phone,
            'description': business.description,
            'status': business.status
        }
    })


# ==================== BUSINESS LOCATIONS ====================

@admin_business_bp.route('/<int:business_id>/locations', methods=['GET'])
@jwt_admin_required
def get_business_locations(business_id):
    """
    Get all locations for a business
    """
    from models import Business, BusinessLocation

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    locations = BusinessLocation.query.filter_by(
        business_id=business_id
    ).order_by(BusinessLocation.name.asc()).all()

    return jsonify({
        'business': {
            'id': business.id,
            'name': business.name
        },
        'locations': [loc.to_dict() for loc in locations]
    })


def auto_geocode_location(address, city):
    """
    Auto-geocode a location using address and city.
    Returns (latitude, longitude) or (None, None) if not found.
    """
    if not address and not city:
        return None, None

    # Build query - try with address first, then city only
    queries_to_try = []
    if address and city:
        queries_to_try.append(f"{address}, {city}, Bosnia and Herzegovina")
        queries_to_try.append(f"{address}, {city}")
    if city:
        queries_to_try.append(f"{city}, Bosnia and Herzegovina")

    # Try Google first, then Nominatim
    for query in queries_to_try:
        result = geocode_with_google(query)
        if result:
            logger.info(f"Auto-geocoded '{query}' via Google -> {result[0]}, {result[1]}")
            return result[0], result[1]

    # Fallback to Nominatim
    for query in queries_to_try:
        result = geocode_with_nominatim(query)
        if result:
            logger.info(f"Auto-geocoded '{query}' via Nominatim -> {result[0]}, {result[1]}")
            return result[0], result[1]

    return None, None


@admin_business_bp.route('/<int:business_id>/locations', methods=['POST'])
@jwt_admin_required
def create_business_location(business_id):
    """
    Create a new location for a business.
    Auto-geocodes using OpenStreetMap if lat/long not provided.
    Body:
    - name: location name (required)
    - address: full street address
    - city: city name
    - latitude: GPS latitude (auto-geocoded if not provided)
    - longitude: GPS longitude (auto-geocoded if not provided)
    - phone: contact phone
    - working_hours: JSON object with hours
    """
    from models import db, Business, BusinessLocation

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Location name is required'}), 400

    address = (data.get('address') or '').strip() or None
    city = (data.get('city') or '').strip() or None
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Auto-geocode if coordinates not provided but address/city are
    geocoded = False
    if (not latitude or not longitude) and (address or city):
        auto_lat, auto_lng = auto_geocode_location(address, city)
        if auto_lat and auto_lng:
            latitude = auto_lat
            longitude = auto_lng
            geocoded = True

    location = BusinessLocation(
        business_id=business_id,
        name=name,
        address=address,
        city=city,
        latitude=latitude,
        longitude=longitude,
        phone=(data.get('phone') or '').strip() or None,
        working_hours=data.get('working_hours'),
        is_active=True
    )

    db.session.add(location)
    db.session.commit()

    log_msg = f"Created location '{name}' for business {business.name}"
    if geocoded:
        log_msg += f" (auto-geocoded to {latitude}, {longitude})"
    logger.info(log_msg)

    return jsonify({
        'success': True,
        'message': f'Location "{name}" created',
        'location': location.to_dict(),
        'geocoded': geocoded
    }), 201


@admin_business_bp.route('/<int:business_id>/locations/<int:location_id>', methods=['PUT'])
@jwt_admin_required
def update_business_location(business_id, location_id):
    """
    Update a business location.
    Auto-geocodes using OpenStreetMap if address/city changed and coords not provided.
    """
    from models import db, BusinessLocation

    location = BusinessLocation.query.filter_by(
        id=location_id,
        business_id=business_id
    ).first()

    if not location:
        return jsonify({'error': 'Location not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Track if address/city changed for auto-geocoding
    address_changed = False
    new_address = location.address
    new_city = location.city

    if 'name' in data:
        name = (data['name'] or '').strip()
        if not name:
            return jsonify({'error': 'Location name cannot be empty'}), 400
        location.name = name
    if 'address' in data:
        new_address = (data['address'] or '').strip() or None
        if new_address != location.address:
            address_changed = True
        location.address = new_address
    if 'city' in data:
        new_city = (data['city'] or '').strip() or None
        if new_city != location.city:
            address_changed = True
        location.city = new_city
    if 'latitude' in data:
        location.latitude = data['latitude']
    if 'longitude' in data:
        location.longitude = data['longitude']
    if 'phone' in data:
        location.phone = (data['phone'] or '').strip() or None
    if 'working_hours' in data:
        location.working_hours = data['working_hours']
    if 'is_active' in data:
        location.is_active = bool(data['is_active'])

    # Auto-geocode if address/city changed and coords not explicitly set
    geocoded = False
    if address_changed and 'latitude' not in data and 'longitude' not in data:
        if new_address or new_city:
            auto_lat, auto_lng = auto_geocode_location(new_address, new_city)
            if auto_lat and auto_lng:
                location.latitude = auto_lat
                location.longitude = auto_lng
                geocoded = True

    location.updated_at = datetime.now()
    db.session.commit()

    log_msg = f"Updated location {location_id} for business {business_id}"
    if geocoded:
        log_msg += f" (auto-geocoded to {location.latitude}, {location.longitude})"
    logger.info(log_msg)

    return jsonify({
        'success': True,
        'message': 'Location updated',
        'location': location.to_dict(),
        'geocoded': geocoded
    })


@admin_business_bp.route('/<int:business_id>/locations/<int:location_id>', methods=['DELETE'])
@jwt_admin_required
def delete_business_location(business_id, location_id):
    """
    Delete a business location
    """
    from models import db, BusinessLocation

    location = BusinessLocation.query.filter_by(
        id=location_id,
        business_id=business_id
    ).first()

    if not location:
        return jsonify({'error': 'Location not found'}), 404

    location_name = location.name

    db.session.delete(location)
    db.session.commit()

    logger.info(f"Deleted location '{location_name}' from business {business_id}")

    return jsonify({
        'success': True,
        'message': f'Location "{location_name}" deleted'
    })


@admin_business_bp.route('/<int:business_id>/locations/bulk', methods=['POST'])
@jwt_admin_required
def bulk_import_locations(business_id):
    """
    Bulk import locations for a business from JSON array.
    Auto-geocodes locations using OpenStreetMap if lat/long not provided.
    Body:
    - locations: array of location objects, each with:
      - name: location name (required)
      - address: full street address
      - city: city name
      - latitude: GPS latitude (auto-geocoded if not provided)
      - longitude: GPS longitude (auto-geocoded if not provided)
      - phone: contact phone
      - working_hours: JSON object with hours
    - auto_geocode: boolean (default true) - whether to auto-geocode missing coords
    """
    import time
    from models import db, Business, BusinessLocation

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    locations_data = data.get('locations', [])
    if not locations_data or not isinstance(locations_data, list):
        return jsonify({'error': 'locations must be a non-empty array'}), 400

    # Option to disable auto-geocoding (default enabled)
    auto_geocode_enabled = data.get('auto_geocode', True)

    created = []
    geocoded_count = 0
    errors = []

    for idx, loc_data in enumerate(locations_data):
        name = (loc_data.get('name') or '').strip()
        if not name:
            errors.append(f"Item {idx + 1}: name is required")
            continue

        try:
            address = (loc_data.get('address') or '').strip() or None
            city = (loc_data.get('city') or '').strip() or None
            latitude = loc_data.get('latitude')
            longitude = loc_data.get('longitude')

            # Auto-geocode if enabled and coords not provided
            was_geocoded = False
            if auto_geocode_enabled and (not latitude or not longitude) and (address or city):
                auto_lat, auto_lng = auto_geocode_location(address, city)
                if auto_lat and auto_lng:
                    latitude = auto_lat
                    longitude = auto_lng
                    was_geocoded = True
                    geocoded_count += 1
                # Rate limit: Nominatim requires 1 sec between requests
                time.sleep(1.1)

            location = BusinessLocation(
                business_id=business_id,
                name=name,
                address=address,
                city=city,
                latitude=latitude,
                longitude=longitude,
                phone=(loc_data.get('phone') or '').strip() or None,
                working_hours=loc_data.get('working_hours'),
                is_active=True
            )
            db.session.add(location)
            db.session.flush()
            created.append({
                'id': location.id,
                'name': location.name,
                'geocoded': was_geocoded,
                'latitude': latitude,
                'longitude': longitude
            })
        except Exception as e:
            errors.append(f"Item {idx + 1} ({name}): {str(e)}")

    if created:
        db.session.commit()
        logger.info(f"Bulk imported {len(created)} locations for business {business.name} ({geocoded_count} auto-geocoded)")

    return jsonify({
        'success': len(created) > 0,
        'created_count': len(created),
        'geocoded_count': geocoded_count,
        'created': created,
        'errors': errors,
        'message': f'Created {len(created)} locations ({geocoded_count} auto-geocoded)' + (f' with {len(errors)} errors' if errors else '')
    }), 201 if created else 400


# ==================== GEOCODING ====================

import os

# Google Geocoding API settings
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

# Nominatim API settings (free, fallback if Google fails)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {
    "User-Agent": "PopustBA/1.0 (contact@popust.ba)"
}


def geocode_with_google(address_query):
    """
    Geocode using Google Geocoding API.
    Returns (latitude, longitude, display_name) or None if not found.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("Google Maps API key not configured")
        return None

    try:
        params = {
            'address': address_query,
            'key': GOOGLE_MAPS_API_KEY,
            'region': 'ba',  # Bias towards Bosnia
            'language': 'bs'  # Bosnian language
        }

        response = requests.get(GOOGLE_GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]
            location = result['geometry']['location']
            return (
                location['lat'],
                location['lng'],
                result.get('formatted_address', '')
            )
        elif data.get('status') == 'ZERO_RESULTS':
            return None
        else:
            logger.warning(f"Google Geocoding API error: {data.get('status')} - {data.get('error_message', '')}")
            return None

    except requests.exceptions.Timeout:
        logger.warning("Google Geocoding API timeout")
        return None
    except Exception as e:
        logger.warning(f"Google Geocoding API error: {e}")
        return None


def geocode_with_nominatim(query):
    """
    Geocode using Nominatim (OpenStreetMap) API.
    Returns (latitude, longitude, display_name) or None if not found.
    """
    try:
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=NOMINATIM_HEADERS,
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        if results:
            result = results[0]
            return (
                float(result['lat']),
                float(result['lon']),
                result.get('display_name', '')
            )
        return None

    except Exception as e:
        logger.warning(f"Nominatim geocoding error: {e}")
        return None


@admin_business_bp.route('/geocode', methods=['POST'])
@jwt_admin_required
def geocode_address():
    """
    Geocode an address to get latitude and longitude.
    Uses Google Geocoding API first, falls back to Nominatim (OpenStreetMap).
    Body:
    - address: street address (optional)
    - city: city name (required)
    - country: country name (default: Bosnia and Herzegovina)
    """
    import re

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    country = data.get('country', 'Bosnia and Herzegovina').strip()

    if not city and not address:
        return jsonify({'error': 'City or address is required'}), 400

    # Helper to strip house numbers from address
    def strip_house_number(addr):
        return re.sub(r'[\s,]+\d+[a-zA-Z]?$', '', addr).strip()

    # Build search queries to try (in order of specificity)
    queries_to_try = []

    if address and city:
        queries_to_try.append(f"{address}, {city}, Bosnia and Herzegovina")
        queries_to_try.append(f"{address}, {city}")
        street_only = strip_house_number(address)
        if street_only != address:
            queries_to_try.append(f"{street_only}, {city}, Bosnia and Herzegovina")
            queries_to_try.append(f"{street_only}, {city}")
    elif city:
        queries_to_try.append(f"{city}, {country}")
        queries_to_try.append(city)

    # Try Google Geocoding API first
    for query in queries_to_try:
        result = geocode_with_google(query)
        if result:
            latitude, longitude, display_name = result
            logger.info(f"Google geocoded '{query}' -> {latitude}, {longitude}")
            return jsonify({
                'success': True,
                'latitude': latitude,
                'longitude': longitude,
                'display_name': display_name,
                'source': 'google'
            })

    # Fall back to Nominatim
    logger.info("Google geocoding failed, trying Nominatim fallback")
    for query in queries_to_try:
        result = geocode_with_nominatim(query)
        if result:
            latitude, longitude, display_name = result
            logger.info(f"Nominatim geocoded '{query}' -> {latitude}, {longitude}")
            return jsonify({
                'success': True,
                'latitude': latitude,
                'longitude': longitude,
                'display_name': display_name,
                'source': 'nominatim'
            })

    return jsonify({
        'success': False,
        'error': 'Adresa nije pronađena. Pokušajte sa preciznijom adresom.'
    }), 404


@admin_business_bp.route('/<int:business_id>/locations/geocode-all', methods=['POST'])
@jwt_admin_required
def geocode_existing_locations(business_id):
    """
    Geocode all existing locations for a business that don't have coordinates.
    Uses OpenStreetMap Nominatim (free) with Google as primary if configured.
    This is useful for bulk-imported locations that need geocoding.
    Body:
    - limit: max locations to process (default 50, max 500)
    - skip_geocoded: whether to skip already geocoded locations (default true)
    """
    import time
    from models import db, Business, BusinessLocation
    from sqlalchemy import or_

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json() or {}
    limit = min(data.get('limit', 50), 500)  # Max 500 per request
    skip_geocoded = data.get('skip_geocoded', True)

    # Query locations without coordinates
    query = BusinessLocation.query.filter_by(business_id=business_id)
    if skip_geocoded:
        query = query.filter(
            or_(
                BusinessLocation.latitude.is_(None),
                BusinessLocation.longitude.is_(None)
            )
        )

    locations = query.limit(limit).all()

    if not locations:
        return jsonify({
            'success': True,
            'message': 'No locations to geocode',
            'processed': 0,
            'geocoded': 0,
            'failed': 0
        })

    processed = 0
    geocoded = 0
    failed = 0
    results = []

    for location in locations:
        processed += 1

        if not location.address and not location.city:
            results.append({
                'id': location.id,
                'name': location.name,
                'status': 'skipped',
                'reason': 'No address or city'
            })
            failed += 1
            continue

        # Auto-geocode
        auto_lat, auto_lng = auto_geocode_location(location.address, location.city)

        if auto_lat and auto_lng:
            location.latitude = auto_lat
            location.longitude = auto_lng
            location.updated_at = datetime.now()
            geocoded += 1
            results.append({
                'id': location.id,
                'name': location.name,
                'status': 'geocoded',
                'latitude': auto_lat,
                'longitude': auto_lng
            })
        else:
            failed += 1
            results.append({
                'id': location.id,
                'name': location.name,
                'status': 'failed',
                'address': location.address,
                'city': location.city
            })

        # Rate limit: Nominatim requires 1 sec between requests
        if processed < len(locations):
            time.sleep(1.1)

    if geocoded > 0:
        db.session.commit()
        logger.info(f"Geocoded {geocoded}/{processed} locations for business {business.name}")

    # Count remaining locations without coordinates
    remaining = BusinessLocation.query.filter_by(business_id=business_id).filter(
        or_(
            BusinessLocation.latitude.is_(None),
            BusinessLocation.longitude.is_(None)
        )
    ).count()

    return jsonify({
        'success': True,
        'message': f'Processed {processed} locations: {geocoded} geocoded, {failed} failed',
        'processed': processed,
        'geocoded': geocoded,
        'failed': failed,
        'remaining': remaining,
        'results': results
    })


# ==================== FEATURED PRODUCTS ====================

@admin_business_bp.route('/<int:business_id>/featured', methods=['GET'])
@jwt_admin_required
def get_featured_products(business_id):
    """
    Get the featured products for a business
    Returns the list of product IDs marked as featured (max 6)
    Auto-cleans stale product IDs that no longer exist
    """
    from app import db
    from models import Business, Product

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    featured_ids = business.featured_products or []

    # Auto-clean: filter out stale product IDs that no longer exist
    if featured_ids:
        valid_ids = [p.id for p in Product.query.filter(
            Product.id.in_(featured_ids),
            Product.business_id == business_id
        ).all()]
        # If there were stale IDs, update the database
        if set(valid_ids) != set(featured_ids):
            business.featured_products = valid_ids
            db.session.commit()
            logger.info(f"Auto-cleaned stale featured products for business {business_id}: {featured_ids} -> {valid_ids}")
            featured_ids = valid_ids

    return jsonify({
        'success': True,
        'featured_products': featured_ids
    })


@admin_business_bp.route('/<int:business_id>/featured', methods=['POST', 'PUT'])
@jwt_admin_required
def set_featured_products(business_id):
    """
    Set the featured products for a business
    Body:
    - product_ids: array of product IDs (max 6)
    """
    from app import db
    from models import Business, Product

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    product_ids = data.get('product_ids', [])

    # Validate max 6 products
    if len(product_ids) > 6:
        return jsonify({'error': 'Maximum 6 featured products allowed'}), 400

    # Filter to only valid product IDs that belong to this business
    if product_ids:
        valid_products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.business_id == business_id
        ).all()
        valid_ids = [p.id for p in valid_products]
        # Keep original order, but only valid ones
        product_ids = [pid for pid in product_ids if pid in valid_ids]

    # Update featured products
    business.featured_products = product_ids
    db.session.commit()

    logger.info(f"Business {business_id} featured products updated: {product_ids}")

    return jsonify({
        'success': True,
        'featured_products': product_ids
    })
