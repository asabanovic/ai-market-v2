"""
Admin API routes for managing business memberships
Uses JWT authentication (not flask_login session)
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
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
