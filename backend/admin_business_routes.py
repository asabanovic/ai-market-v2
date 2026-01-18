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


@admin_business_bp.route('/<int:business_id>/locations', methods=['POST'])
@jwt_admin_required
def create_business_location(business_id):
    """
    Create a new location for a business
    Body:
    - name: location name (required)
    - address: full street address
    - city: city name
    - latitude: GPS latitude
    - longitude: GPS longitude
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

    location = BusinessLocation(
        business_id=business_id,
        name=name,
        address=data.get('address', '').strip() or None,
        city=data.get('city', '').strip() or None,
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        phone=data.get('phone', '').strip() or None,
        working_hours=data.get('working_hours'),
        is_active=True
    )

    db.session.add(location)
    db.session.commit()

    logger.info(f"Created location '{name}' for business {business.name}")

    return jsonify({
        'success': True,
        'message': f'Location "{name}" created',
        'location': location.to_dict()
    }), 201


@admin_business_bp.route('/<int:business_id>/locations/<int:location_id>', methods=['PUT'])
@jwt_admin_required
def update_business_location(business_id, location_id):
    """
    Update a business location
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

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Location name cannot be empty'}), 400
        location.name = name
    if 'address' in data:
        location.address = data['address'].strip() or None
    if 'city' in data:
        location.city = data['city'].strip() or None
    if 'latitude' in data:
        location.latitude = data['latitude']
    if 'longitude' in data:
        location.longitude = data['longitude']
    if 'phone' in data:
        location.phone = data['phone'].strip() or None
    if 'working_hours' in data:
        location.working_hours = data['working_hours']
    if 'is_active' in data:
        location.is_active = bool(data['is_active'])

    location.updated_at = datetime.now()
    db.session.commit()

    logger.info(f"Updated location {location_id} for business {business_id}")

    return jsonify({
        'success': True,
        'message': 'Location updated',
        'location': location.to_dict()
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


# ==================== GEOCODING ====================

# Nominatim API settings (free, no API key required)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {
    "User-Agent": "PopustBA/1.0 (contact@popust.ba)"
}


@admin_business_bp.route('/geocode', methods=['POST'])
@jwt_admin_required
def geocode_address():
    """
    Geocode an address to get latitude and longitude using Nominatim (OpenStreetMap)
    Body:
    - address: street address (optional)
    - city: city name (required)
    - country: country name (default: Bosnia and Herzegovina)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    country = data.get('country', 'Bosnia and Herzegovina').strip()

    if not city and not address:
        return jsonify({'error': 'City or address is required'}), 400

    # Build search query
    query_parts = []
    if address:
        query_parts.append(address)
    if city:
        query_parts.append(city)
    if country:
        query_parts.append(country)

    query = ', '.join(query_parts)

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

        if not results:
            # Try without country if no results
            if country and city:
                params['q'] = f"{address}, {city}" if address else city
                response = requests.get(
                    NOMINATIM_URL,
                    params=params,
                    headers=NOMINATIM_HEADERS,
                    timeout=10
                )
                results = response.json()

        if not results:
            return jsonify({
                'success': False,
                'error': 'Adresa nije pronađena. Pokušajte sa preciznijom adresom.'
            }), 404

        result = results[0]
        latitude = float(result['lat'])
        longitude = float(result['lon'])
        display_name = result.get('display_name', '')

        logger.info(f"Geocoded '{query}' -> {latitude}, {longitude}")

        return jsonify({
            'success': True,
            'latitude': latitude,
            'longitude': longitude,
            'display_name': display_name
        })

    except requests.exceptions.Timeout:
        logger.error(f"Geocoding timeout for: {query}")
        return jsonify({'error': 'Geocoding service timeout'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding error for {query}: {e}")
        return jsonify({'error': 'Geocoding service error'}), 500
    except Exception as e:
        logger.error(f"Unexpected geocoding error: {e}", exc_info=True)
        return jsonify({'error': 'Unexpected error during geocoding'}), 500
