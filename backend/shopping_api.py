"""
Shopping List and Favorites API
REST endpoints for shopping cart and favorites functionality
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from app import app, db
from auth_api import require_jwt_auth
from models import (User, Product, Business, Favorite, ShoppingList,
                    ShoppingListItem, SMSOutbox)
from credits_service import CreditsService, InsufficientCreditsError
from sms_service import sms_service
import logging

logger = logging.getLogger(__name__)

# Create blueprint
shopping_api_bp = Blueprint('shopping_api', __name__, url_prefix='/api')

# ==================== FAVORITES ENDPOINTS ====================

@shopping_api_bp.route('/favorites', methods=['POST'])
@require_jwt_auth
def add_favorite():
    """
    Add a product to user's favorites
    Cost: 1 credit (first add only, idempotent)
    """
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data or 'product_id' not in data:
            return jsonify({'error': 'product_id is required'}), 400

        product_id = data['product_id']

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Check if already favorited (idempotent)
        existing = Favorite.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if existing:
            # Already favorited - don't charge credits
            return jsonify({
                'ok': True,
                'already': True,
                'favorite_id': existing.id,
                'message': 'Proizvod je već u omiljenim'
            }), 200

        # Deduct 1 credit
        try:
            result = CreditsService.deduct_credits(
                user_id=user_id,
                amount=1,
                action='ADD_FAVORITE',
                metadata={'product_id': product_id}
            )
        except InsufficientCreditsError as e:
            return jsonify({
                'code': 'INSUFFICIENT_CREDITS',
                'needs_topup': True,
                'credits_left': e.credits_available,
                'message': 'Nemate dovoljno kredita'
            }), 402

        # Create favorite
        favorite = Favorite(
            user_id=user_id,
            product_id=product_id
        )

        db.session.add(favorite)
        db.session.commit()

        logger.info(f"User {user_id} added favorite {product_id}")

        return jsonify({
            'ok': True,
            'favorite_id': favorite.id,
            'credits_left': result['balance']
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding favorite: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/favorites', methods=['GET'])
@require_jwt_auth
def get_favorites():
    """Get user's favorites list with product summaries"""
    try:
        user_id = request.current_user_id

        favorites = Favorite.query.filter_by(user_id=user_id).join(
            Product
        ).join(Business).order_by(Favorite.created_at.desc()).all()

        result = []
        for fav in favorites:
            product = fav.product
            business = product.business

            # Calculate current price
            price = product.discount_price if product.has_discount else product.base_price

            result.append({
                'favorite_id': fav.id,
                'product_id': product.id,
                'name': product.title,
                'image_url': product.image_path,
                'category': product.category,
                'price': price,
                'old_price': product.base_price if product.has_discount else None,
                'discount_percent': product.discount_percentage if product.has_discount else None,
                'business': {
                    'id': business.id,
                    'name': business.name,
                    'logo': business.logo_path
                },
                'created_at': fav.created_at.isoformat()
            })

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@require_jwt_auth
def remove_favorite(favorite_id):
    """Remove a favorite (no credit refund)"""
    try:
        user_id = request.current_user_id

        favorite = Favorite.query.filter_by(
            id=favorite_id,
            user_id=user_id
        ).first()

        if not favorite:
            return jsonify({'error': 'Favorite not found'}), 404

        db.session.delete(favorite)
        db.session.commit()

        logger.info(f"User {user_id} removed favorite {favorite_id}")

        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing favorite: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== SHOPPING LIST ENDPOINTS ====================

def get_or_create_active_list(user_id: str) -> ShoppingList:
    """Get user's active shopping list or create a new one"""
    # Check for existing active list
    active_list = ShoppingList.query.filter_by(
        user_id=user_id,
        status='ACTIVE'
    ).filter(
        ShoppingList.expires_at > datetime.now()
    ).first()

    if active_list:
        return active_list

    # Create new list with 24-hour expiry
    new_list = ShoppingList(
        user_id=user_id,
        status='ACTIVE',
        expires_at=datetime.now() + timedelta(hours=24)
    )

    db.session.add(new_list)
    db.session.commit()

    logger.info(f"Created new shopping list {new_list.id} for user {user_id}")

    return new_list


@shopping_api_bp.route('/shopping-list/items', methods=['POST'])
@require_jwt_auth
def add_to_shopping_list():
    """
    Add item to shopping list
    Cost: 1 credit per add
    Max 10 distinct items per list
    """
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data or 'product_id' not in data or 'offer_id' not in data:
            return jsonify({'error': 'product_id and offer_id are required'}), 400

        product_id = data['product_id']
        offer_id = data['offer_id']  # This is the business_id for store-specific offer
        qty = data.get('qty', 1)

        if qty < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400

        # Verify product and business exist
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        business = Business.query.get(offer_id)
        if not business:
            return jsonify({'error': 'Store not found'}), 404

        # Get or create active list
        shopping_list = get_or_create_active_list(user_id)

        # Check if this item already exists in the list
        existing_item = ShoppingListItem.query.filter_by(
            list_id=shopping_list.id,
            product_id=product_id,
            business_id=offer_id
        ).first()

        if existing_item:
            # Item exists - just increment quantity (no credit charge, no item limit check)
            existing_item.qty += qty
            existing_item.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"Increased qty for item {existing_item.id} to {existing_item.qty}")

            return jsonify({
                'ok': True,
                'list_id': shopping_list.id,
                'item_id': existing_item.id,
                'ttl_seconds': shopping_list.ttl_seconds,
                'credits_left': CreditsService.get_balance(user_id)
            }), 200

        # New item - check 10 item limit
        item_count = ShoppingListItem.query.filter_by(
            list_id=shopping_list.id
        ).count()

        if item_count >= 10:
            return jsonify({
                'code': 'LIST_ITEM_LIMIT',
                'limit': 10,
                'message': 'Dostigli ste limit od 10 artikala u listi'
            }), 400

        # Deduct 1 credit
        try:
            credit_result = CreditsService.deduct_credits(
                user_id=user_id,
                amount=1,
                action='ADD_TO_CART',
                metadata={
                    'product_id': product_id,
                    'business_id': offer_id,
                    'list_id': shopping_list.id
                }
            )
        except InsufficientCreditsError as e:
            return jsonify({
                'code': 'INSUFFICIENT_CREDITS',
                'needs_topup': True,
                'credits_left': e.credits_available,
                'message': 'Nemate dovoljno kredita'
            }), 402

        # Snapshot current prices
        price_snapshot = product.discount_price if product.has_discount else product.base_price
        old_price_snapshot = product.base_price if product.has_discount else None
        discount_percent = product.discount_percentage if product.has_discount else None

        # Create new item
        new_item = ShoppingListItem(
            list_id=shopping_list.id,
            product_id=product_id,
            business_id=offer_id,
            qty=qty,
            price_snapshot=price_snapshot,
            old_price_snapshot=old_price_snapshot,
            discount_percent_snapshot=discount_percent
        )

        db.session.add(new_item)
        db.session.commit()

        logger.info(f"Added item {new_item.id} to list {shopping_list.id}")

        return jsonify({
            'ok': True,
            'list_id': shopping_list.id,
            'item_id': new_item.id,
            'ttl_seconds': shopping_list.ttl_seconds,
            'credits_left': credit_result['balance']
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding to shopping list: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/shopping-list/items/<int:item_id>', methods=['PATCH'])
@require_jwt_auth
def update_shopping_list_item(item_id):
    """Update quantity of a shopping list item"""
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data or 'qty' not in data:
            return jsonify({'error': 'qty is required'}), 400

        qty = data['qty']
        print("QTY: ", qty)
        # Get item and verify ownership
        item = ShoppingListItem.query.join(ShoppingList).filter(
            ShoppingListItem.id == item_id,
            ShoppingList.user_id == user_id,
            ShoppingList.status == 'ACTIVE'
        ).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if qty == 0:
            # Remove item
            db.session.delete(item)
            db.session.commit()
            logger.info(f"Removed item {item_id}")
            return '', 204
        elif qty > 0:
            # Update quantity
            item.qty = qty
            item.updated_at = datetime.now()
            db.session.commit()
            logger.info(f"Updated item {item_id} qty to {qty}")
            return jsonify({'ok': True}), 200
        else:
            return jsonify({'error': 'Quantity must be 0 or positive'}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating shopping list item: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/shopping-list/items/<int:item_id>', methods=['DELETE'])
@require_jwt_auth
def remove_shopping_list_item(item_id):
    """Remove an item from shopping list"""
    try:
        user_id = request.current_user_id
        # Get item and verify ownership
        item = ShoppingListItem.query.join(ShoppingList).filter(
            ShoppingListItem.id == item_id,
            ShoppingList.user_id == user_id,
            ShoppingList.status == 'ACTIVE'
        ).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        db.session.delete(item)
        db.session.commit()

        logger.info(f"Removed item {item_id} from shopping list")

        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing shopping list item: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/shopping-list/header/ttl', methods=['GET'])
@require_jwt_auth
def get_shopping_list_header():
    """Get TTL and item count for header badge"""
    try:
        user_id = request.current_user_id

        # Get active list
        active_list = ShoppingList.query.filter_by(
            user_id=user_id,
            status='ACTIVE'
        ).filter(
            ShoppingList.expires_at > datetime.now()
        ).first()

        if not active_list:
            return jsonify({
                'ttl_seconds': None,
                'item_count': 0
            }), 200

        # Count items
        item_count = ShoppingListItem.query.filter_by(
            list_id=active_list.id
        ).count()

        return jsonify({
            'ttl_seconds': active_list.ttl_seconds,
            'item_count': item_count
        }), 200

    except Exception as e:
        logger.error(f"Error getting shopping list header: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/shopping-list/sidebar', methods=['GET'])
@require_jwt_auth
def get_shopping_list_sidebar():
    """Get full shopping list with grouped receipt view"""
    try:
        user_id = request.current_user_id

        # Get active list
        active_list = ShoppingList.query.filter_by(
            user_id=user_id,
            status='ACTIVE'
        ).filter(
            ShoppingList.expires_at > datetime.now()
        ).first()

        if not active_list:
            return jsonify({
                'list_id': None,
                'ttl_seconds': None,
                'groups': [],
                'total_items': 0,
                'grand_total': 0,
                'grand_saving': 0
            }), 200

        # Get all items with product and business info
        items = ShoppingListItem.query.filter_by(
            list_id=active_list.id
        ).join(Product).join(Business).all()

        # Group items by business
        groups_dict = {}
        total_items = 0
        grand_total = 0
        grand_saving = 0

        for item in items:
            business_id = item.business_id
            business = item.business

            if business_id not in groups_dict:
                groups_dict[business_id] = {
                    'store': {
                        'id': business.id,
                        'name': business.name,
                        'logo': business.logo_path
                    },
                    'items': [],
                    'group_subtotal': 0,
                    'group_saving': 0
                }

            # Calculate item totals
            subtotal = item.subtotal
            saving = item.estimated_saving

            groups_dict[business_id]['items'].append({
                'item_id': item.id,
                'product_id': item.product_id,
                'name': item.product.title,
                'qty': item.qty,
                'unit_price': item.price_snapshot,
                'subtotal': subtotal,
                'old_price': item.old_price_snapshot,
                'estimated_saving': saving
            })

            groups_dict[business_id]['group_subtotal'] += subtotal
            groups_dict[business_id]['group_saving'] += saving

            total_items += item.qty
            grand_total += subtotal
            grand_saving += saving

        # Convert dict to list
        groups = list(groups_dict.values())

        # Round all monetary values
        grand_total = round(grand_total, 2)
        grand_saving = round(grand_saving, 2)
        for group in groups:
            group['group_subtotal'] = round(group['group_subtotal'], 2)
            group['group_saving'] = round(group['group_saving'], 2)

        return jsonify({
            'list_id': active_list.id,
            'ttl_seconds': active_list.ttl_seconds,
            'groups': groups,
            'total_items': total_items,
            'grand_total': grand_total,
            'grand_saving': grand_saving
        }), 200

    except Exception as e:
        logger.error(f"Error getting shopping list sidebar: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@shopping_api_bp.route('/shopping-list/<int:list_id>/checkout', methods=['POST'])
@require_jwt_auth
def checkout_shopping_list(list_id):
    """
    Checkout shopping list
    Cost: 0 credits (promo)
    Queues SMS with receipt
    """
    try:
        user_id = request.current_user_id
        data = request.get_json() or {}

        # Get list and verify ownership
        shopping_list = ShoppingList.query.filter_by(
            id=list_id,
            user_id=user_id,
            status='ACTIVE'
        ).first()

        if not shopping_list:
            return jsonify({'error': 'Shopping list not found'}), 404

        # Check if expired
        if not shopping_list.is_active:
            return jsonify({'error': 'Shopping list has expired'}), 400

        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check for phone number
        phone = data.get('phone') or user.phone

        if not phone:
            return jsonify({
                'error': 'Phone number is required',
                'needs_phone': True
            }), 400

        # Validate phone number
        is_valid, formatted_phone, error_msg = sms_service.validate_phone_number(phone)
        if not is_valid:
            return jsonify({
                'error': error_msg,
                'needs_phone': True
            }), 400

        # Save phone to user profile if not already set
        if not user.phone:
            user.phone = formatted_phone
            db.session.commit()

        # Get receipt data for SMS
        receipt_response = get_shopping_list_sidebar()
        receipt_data = receipt_response[0].get_json()

        # Format SMS body
        sms_body = sms_service.format_receipt_sms(receipt_data)

        # Queue SMS
        sms_result = sms_service.send_sms_now(
            user_id=user_id,
            phone=formatted_phone,
            body=sms_body,
            list_id=list_id
        )

        # Record free transaction (promo)
        CreditsService.record_free_transaction(
            user_id=user_id,
            action='CHECKOUT_SMS',
            metadata={
                'list_id': list_id,
                'promo': True,
                'sms_id': sms_result['sms_id']
            }
        )

        # Update list status
        shopping_list.status = 'SENT'
        shopping_list.sent_at = datetime.now()
        db.session.commit()

        logger.info(f"Checkout completed for list {list_id}. SMS queued: {sms_result['sms_id']}")

        return jsonify({
            'queued': True,
            'checkout_fee_ui': {
                'original': 5,
                'final': 0,
                'promo': True
            },
            'ttl_seconds': shopping_list.ttl_seconds,
            'sms_status': sms_result['status']
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking out shopping list: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== HISTORICAL LISTS ====================

@shopping_api_bp.route('/shopping-lists/history', methods=['GET'])
@require_jwt_auth
def get_shopping_history():
    """
    Get user's historical shopping lists (EXPIRED, SENT)
    Read-only view for historical purposes
    """
    try:
        user_id = request.current_user_id
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Get all non-active lists (EXPIRED, SENT)
        historical_lists = ShoppingList.query.filter(
            ShoppingList.user_id == user_id,
            ShoppingList.status.in_(['EXPIRED', 'SENT'])
        ).order_by(ShoppingList.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Format response
        lists_data = []
        for shopping_list in historical_lists.items:
            # Get items for this list
            items = ShoppingListItem.query.filter_by(
                list_id=shopping_list.id
            ).all()

            # Group by business
            business_groups = {}
            total_amount = 0
            total_savings = 0
            item_count = 0

            for item in items:
                business_id = item.business_id
                if business_id not in business_groups:
                    business = Business.query.get(business_id)
                    business_groups[business_id] = {
                        'business': {
                            'id': business.id,
                            'name': business.name,
                            'logo': business.logo_path,
                            'city': business.city
                        },
                        'items': [],
                        'subtotal': 0
                    }

                # Get product details
                product = Product.query.get(item.product_id)
                item_total = item.price_snapshot * item.qty

                business_groups[business_id]['items'].append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.title if product else 'Unknown',
                    'qty': item.qty,
                    'price': item.price_snapshot,
                    'old_price': item.old_price_snapshot,
                    'discount_percent': item.discount_percent_snapshot,
                    'total': item_total
                })

                business_groups[business_id]['subtotal'] += item_total
                total_amount += item_total
                item_count += item.qty

                # Calculate savings
                if item.old_price_snapshot and item.old_price_snapshot > item.price_snapshot:
                    savings_per_item = (item.old_price_snapshot - item.price_snapshot) * item.qty
                    total_savings += savings_per_item

            lists_data.append({
                'id': shopping_list.id,
                'status': shopping_list.status,
                'created_at': shopping_list.created_at.isoformat(),
                'expires_at': shopping_list.expires_at.isoformat() if shopping_list.expires_at else None,
                'sent_at': shopping_list.sent_at.isoformat() if shopping_list.sent_at else None,
                'item_count': item_count,
                'total_amount': round(total_amount, 2),
                'total_savings': round(total_savings, 2),
                'groups': list(business_groups.values())
            })

        return jsonify({
            'lists': lists_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': historical_lists.total,
                'pages': historical_lists.pages,
                'has_next': historical_lists.has_next,
                'has_prev': historical_lists.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting shopping history: {e}")
        return jsonify({'error': 'Internal server error'}), 500
