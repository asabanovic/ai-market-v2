"""
Product duplicate detection and merging utilities.

This module provides functions to:
1. Detect duplicate products within a store based on normalized title similarity
2. Merge duplicate products while preserving price history
3. Preview potential duplicates before bulk import
"""

import re
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from app import db
from models import Product, ProductPriceHistory, Favorite, ShoppingListItem, ProductMatch, ProductEmbedding, UserEngagement


def normalize_title(title: str) -> str:
    """
    Normalize a product title for comparison.
    - Lowercase
    - Remove extra spaces
    - Normalize Unicode characters
    - Standardize punctuation
    - Remove common suffixes/prefixes that vary
    """
    if not title:
        return ""

    # Lowercase
    normalized = title.lower().strip()

    # Normalize Unicode (handle accents, etc.)
    normalized = unicodedata.normalize('NFKD', normalized)

    # Standardize common variations
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)

    # Standardize common unit variations
    normalized = re.sub(r'(\d+)\s*(ml|l|g|kg|kom)', r'\1\2', normalized)  # Remove space before unit
    normalized = re.sub(r'(\d+),(\d+)', r'\1.\2', normalized)  # Normalize decimal separator

    # Standardize percentage notation
    normalized = re.sub(r'(\d+),(\d+)\s*%', r'\1.\2%', normalized)
    normalized = re.sub(r'(\d+)\s*%', r'\1%', normalized)  # Remove space before %

    # Remove trailing punctuation
    normalized = re.sub(r'[,\.;:]+$', '', normalized)

    return normalized


def extract_key_components(title: str) -> Dict:
    """
    Extract key components from a product title for matching.
    Returns dict with: brand, product_type, size, variant
    """
    normalized = normalize_title(title)

    components = {
        'normalized': normalized,
        'brand': None,
        'size': None,
        'percentage': None,
    }

    # Extract size (e.g., "1l", "500ml", "200g", "1kg")
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|l|g|kg|kom)', normalized, re.IGNORECASE)
    if size_match:
        value = float(size_match.group(1))
        unit = size_match.group(2).lower()
        # Normalize to standard units
        if unit == 'ml' and value >= 1000:
            value = value / 1000
            unit = 'l'
        elif unit == 'g' and value >= 1000:
            value = value / 1000
            unit = 'kg'
        components['size'] = f"{value:g}{unit}"

    # Extract percentage (e.g., "2.8%", "3.2%")
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', normalized)
    if pct_match:
        components['percentage'] = f"{float(pct_match.group(1)):g}%"

    return components


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity score between two product titles.
    Returns a score between 0 and 1.
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    if norm1 == norm2:
        return 1.0

    # Check if one is substring of other
    if norm1 in norm2 or norm2 in norm1:
        # Calculate based on length ratio
        min_len = min(len(norm1), len(norm2))
        max_len = max(len(norm1), len(norm2))
        return min_len / max_len if max_len > 0 else 0

    # Word-based similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return 0

    intersection = words1 & words2
    union = words1 | words2

    # Jaccard similarity
    jaccard = len(intersection) / len(union) if union else 0

    # Weighted by key components matching
    comp1 = extract_key_components(title1)
    comp2 = extract_key_components(title2)

    component_bonus = 0
    if comp1['size'] and comp1['size'] == comp2['size']:
        component_bonus += 0.2
    if comp1['percentage'] and comp1['percentage'] == comp2['percentage']:
        component_bonus += 0.1

    return min(1.0, jaccard + component_bonus)


def find_duplicates_in_business(business_id: int, similarity_threshold: float = 0.85) -> List[Dict]:
    """
    Find potential duplicate products within a business.
    Groups products that appear to be duplicates.

    Returns list of duplicate groups:
    [{
        'products': [product_dicts],
        'normalized_title': str,
        'similarity': float,
        'recommended_keep': product_id  # The one to keep (oldest or most complete)
    }]
    """
    products = Product.query.filter_by(business_id=business_id).all()

    if not products:
        return []

    # Group by normalized title
    groups = defaultdict(list)
    for product in products:
        norm_title = normalize_title(product.title)
        groups[norm_title].append(product)

    # Find exact duplicates (same normalized title)
    duplicates = []
    for norm_title, group in groups.items():
        if len(group) > 1:
            # Sort by created_at (oldest first) and completeness
            sorted_group = sorted(group, key=lambda p: (
                -1 if p.image_path else 0,  # Products with images first
                p.created_at or datetime.min  # Then by oldest
            ))

            duplicates.append({
                'products': [_product_to_dict(p) for p in sorted_group],
                'normalized_title': norm_title,
                'similarity': 1.0,
                'recommended_keep': sorted_group[0].id,
                'match_type': 'exact'
            })

    # Find similar products (fuzzy matching)
    # This is more expensive, so we only check products not already in exact groups
    processed_ids = set()
    for dup in duplicates:
        for p in dup['products']:
            processed_ids.add(p['id'])

    remaining_products = [p for p in products if p.id not in processed_ids]

    # Compare remaining products pairwise (optimization: only compare within same category)
    category_groups = defaultdict(list)
    for product in remaining_products:
        # Use first word or category as grouping key for efficiency
        key = (product.category or normalize_title(product.title).split()[0] if product.title else 'unknown')
        category_groups[key].append(product)

    for key, cat_products in category_groups.items():
        for i, p1 in enumerate(cat_products):
            for p2 in cat_products[i+1:]:
                similarity = calculate_title_similarity(p1.title, p2.title)
                if similarity >= similarity_threshold:
                    # Check if already found
                    existing_group = None
                    for dup in duplicates:
                        if dup['match_type'] == 'fuzzy' and (
                            any(pd['id'] == p1.id for pd in dup['products']) or
                            any(pd['id'] == p2.id for pd in dup['products'])
                        ):
                            existing_group = dup
                            break

                    if existing_group:
                        # Add to existing group
                        if not any(pd['id'] == p1.id for pd in existing_group['products']):
                            existing_group['products'].append(_product_to_dict(p1))
                        if not any(pd['id'] == p2.id for pd in existing_group['products']):
                            existing_group['products'].append(_product_to_dict(p2))
                    else:
                        # Create new group
                        sorted_pair = sorted([p1, p2], key=lambda p: (
                            -1 if p.image_path else 0,
                            p.created_at or datetime.min
                        ))
                        duplicates.append({
                            'products': [_product_to_dict(p) for p in sorted_pair],
                            'normalized_title': normalize_title(p1.title),
                            'similarity': similarity,
                            'recommended_keep': sorted_pair[0].id,
                            'match_type': 'fuzzy'
                        })

    return duplicates


def _product_to_dict(product: Product) -> Dict:
    """Convert a product to a dictionary for API response."""
    return {
        'id': product.id,
        'title': product.title,
        'base_price': product.base_price,
        'discount_price': product.discount_price,
        'image_path': product.image_path,
        'category': product.category,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'expires': product.expires.isoformat() if product.expires else None,
        'has_discount': product.has_discount,
        'discount_percentage': product.discount_percentage,
    }


def merge_products(keep_id: int, merge_ids: List[int], delete_merged: bool = True) -> Dict:
    """
    Merge multiple products into one, preserving all price history.

    Args:
        keep_id: The product ID to keep
        merge_ids: List of product IDs to merge into the kept product
        delete_merged: If True, delete merged products. If False, archive them.

    Returns:
        Dict with merge results
    """
    keep_product = Product.query.get(keep_id)
    if not keep_product:
        return {'success': False, 'error': f'Product {keep_id} not found'}

    merge_products_list = Product.query.filter(Product.id.in_(merge_ids)).all()
    if not merge_products_list:
        return {'success': False, 'error': 'No products to merge found'}

    # Verify all products are from same business
    business_ids = set([keep_product.business_id] + [p.business_id for p in merge_products_list])
    if len(business_ids) > 1:
        return {'success': False, 'error': 'Cannot merge products from different businesses'}

    merged_count = 0
    history_transferred = 0
    favorites_transferred = 0
    cart_items_transferred = 0

    try:
        for merge_product in merge_products_list:
            if merge_product.id == keep_id:
                continue

            # 1. Transfer price history
            existing_history = ProductPriceHistory.query.filter_by(product_id=merge_product.id).all()
            for history in existing_history:
                history.product_id = keep_id
                history_transferred += 1

            # Add current prices as history entry before merge
            if merge_product.base_price != keep_product.base_price or merge_product.discount_price != keep_product.discount_price:
                new_history = ProductPriceHistory(
                    product_id=keep_id,
                    base_price=merge_product.base_price,
                    discount_price=merge_product.discount_price,
                    recorded_at=merge_product.created_at or datetime.now()
                )
                db.session.add(new_history)
                history_transferred += 1

            # 2. Transfer favorites
            favorites = Favorite.query.filter_by(product_id=merge_product.id).all()
            for favorite in favorites:
                # Check if user already has the kept product as favorite
                existing = Favorite.query.filter_by(
                    user_id=favorite.user_id,
                    product_id=keep_id
                ).first()
                if not existing:
                    favorite.product_id = keep_id
                    favorites_transferred += 1
                else:
                    db.session.delete(favorite)

            # 3. Transfer shopping list items
            cart_items = ShoppingListItem.query.filter_by(product_id=merge_product.id).all()
            for item in cart_items:
                # Check if same product already in same list
                existing = ShoppingListItem.query.filter_by(
                    list_id=item.list_id,
                    product_id=keep_id,
                    business_id=item.business_id
                ).first()
                if not existing:
                    item.product_id = keep_id
                    cart_items_transferred += 1
                else:
                    # Add quantities
                    existing.qty += item.qty
                    db.session.delete(item)

            # 4. Transfer product matches (handle unique constraint)
            matches_a = ProductMatch.query.filter_by(product_a_id=merge_product.id).all()
            for match in matches_a:
                if match.product_b_id == keep_id:
                    # This match is between the products being merged - delete it
                    db.session.delete(match)
                else:
                    # Check if a match already exists between keep_id and product_b_id
                    existing = ProductMatch.query.filter_by(
                        product_a_id=keep_id,
                        product_b_id=match.product_b_id,
                        match_type=match.match_type
                    ).first()
                    if existing:
                        db.session.delete(match)
                    else:
                        match.product_a_id = keep_id

            matches_b = ProductMatch.query.filter_by(product_b_id=merge_product.id).all()
            for match in matches_b:
                if match.product_a_id == keep_id:
                    # This match is between the products being merged - delete it
                    db.session.delete(match)
                else:
                    # Check if a match already exists between product_a_id and keep_id
                    existing = ProductMatch.query.filter_by(
                        product_a_id=match.product_a_id,
                        product_b_id=keep_id,
                        match_type=match.match_type
                    ).first()
                    if existing:
                        db.session.delete(match)
                    else:
                        match.product_b_id = keep_id

            # 5. Update kept product with best data from merged
            # Take image if kept product doesn't have one
            if not keep_product.image_path and merge_product.image_path:
                keep_product.image_path = merge_product.image_path

            # Take category if kept product doesn't have one
            if not keep_product.category and merge_product.category:
                keep_product.category = merge_product.category

            # Take enriched description if kept doesn't have one
            if not keep_product.enriched_description and merge_product.enriched_description:
                keep_product.enriched_description = merge_product.enriched_description

            # Take brand/product_type if not set
            if not keep_product.brand and merge_product.brand:
                keep_product.brand = merge_product.brand
            if not keep_product.product_type and merge_product.product_type:
                keep_product.product_type = merge_product.product_type
            if keep_product.size_value is None and merge_product.size_value:
                keep_product.size_value = merge_product.size_value
            if not keep_product.size_unit and merge_product.size_unit:
                keep_product.size_unit = merge_product.size_unit

            # 6. Delete embedding for merged product
            ProductEmbedding.query.filter_by(product_id=merge_product.id).delete()

            # 7. Transfer or delete user engagements
            engagements = UserEngagement.query.filter_by(product_id=merge_product.id).all()
            for engagement in engagements:
                engagement.product_id = keep_id

            # 8. Delete or archive the merged product
            if delete_merged:
                db.session.delete(merge_product)
            else:
                # Archive by setting a special category
                merge_product.category = f"[MERGED INTO {keep_id}] {merge_product.category or ''}"

            merged_count += 1

        # Update match key for kept product
        keep_product.update_match_key()

        db.session.commit()

        return {
            'success': True,
            'kept_product_id': keep_id,
            'merged_count': merged_count,
            'history_transferred': history_transferred,
            'favorites_transferred': favorites_transferred,
            'cart_items_transferred': cart_items_transferred
        }

    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def preview_import_duplicates(business_id: int, products_data: List[Dict]) -> Dict:
    """
    Preview potential duplicates before bulk import.
    Compares incoming products against existing products and against each other.

    Returns:
        {
            'incoming_vs_existing': [{incoming_idx, existing_product, similarity}],
            'incoming_duplicates': [{indices: [idx1, idx2], similarity}]
        }
    """
    # Get existing products
    existing_products = Product.query.filter_by(business_id=business_id).all()
    existing_by_norm_title = {}
    for p in existing_products:
        norm = normalize_title(p.title)
        if norm not in existing_by_norm_title:
            existing_by_norm_title[norm] = []
        existing_by_norm_title[norm].append(p)

    incoming_vs_existing = []
    incoming_duplicates = []

    # Check incoming against existing
    for idx, incoming in enumerate(products_data):
        incoming_title = incoming.get('title', '')
        norm_incoming = normalize_title(incoming_title)

        # Exact match
        if norm_incoming in existing_by_norm_title:
            for existing in existing_by_norm_title[norm_incoming]:
                incoming_vs_existing.append({
                    'incoming_index': idx,
                    'incoming_title': incoming_title,
                    'existing_product': _product_to_dict(existing),
                    'similarity': 1.0,
                    'match_type': 'exact'
                })
        else:
            # Fuzzy match against existing
            for norm_existing, existing_list in existing_by_norm_title.items():
                similarity = calculate_title_similarity(incoming_title, existing_list[0].title)
                if similarity >= 0.85:
                    for existing in existing_list:
                        incoming_vs_existing.append({
                            'incoming_index': idx,
                            'incoming_title': incoming_title,
                            'existing_product': _product_to_dict(existing),
                            'similarity': similarity,
                            'match_type': 'fuzzy'
                        })

    # Check incoming against each other
    for i, p1 in enumerate(products_data):
        for j, p2 in enumerate(products_data[i+1:], start=i+1):
            title1 = p1.get('title', '')
            title2 = p2.get('title', '')
            similarity = calculate_title_similarity(title1, title2)
            if similarity >= 0.85:
                incoming_duplicates.append({
                    'indices': [i, j],
                    'titles': [title1, title2],
                    'similarity': similarity
                })

    return {
        'incoming_vs_existing': incoming_vs_existing,
        'incoming_duplicates': incoming_duplicates
    }
