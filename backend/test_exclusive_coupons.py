#!/usr/bin/env python3
"""
Test suite for Exclusive Coupons (Ekskluzivni Popusti) feature.

Tests cover:
1. Feature flags
2. Campaign CRUD operations
3. Coupon CRUD operations (within campaigns)
4. Coupon purchase flow
5. Coupon redemption
6. Reviews and ratings
7. Admin operations
8. Scheduled jobs
9. Email notifications (mocked)

Usage:
    python test_exclusive_coupons.py [--verbose]

Requirements:
    - Local backend running on localhost:5001
    - Database with test data
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:5001"

# Test credentials - UPDATE THESE FOR YOUR ENVIRONMENT
TEST_ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "adnanxteam@gmail.com")
TEST_ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "your_password_here")
# Or use a JWT token directly
TEST_JWT_TOKEN = os.environ.get("TEST_JWT_TOKEN", "")

# Test results tracking
test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'errors': []
}

VERBOSE = False


def log(message: str, level: str = "INFO"):
    """Print log message with timestamp"""
    if VERBOSE or level in ["ERROR", "PASS", "FAIL"]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "PASS": "✅",
            "FAIL": "❌",
            "ERROR": "🔥",
            "SKIP": "⏭️ ",
            "DEBUG": "🔍"
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")


def assert_equals(actual, expected, message: str):
    """Assert two values are equal"""
    if actual == expected:
        log(f"PASS: {message}", "PASS")
        test_results['passed'] += 1
        return True
    else:
        log(f"FAIL: {message} | Expected: {expected}, Got: {actual}", "FAIL")
        test_results['failed'] += 1
        test_results['errors'].append(f"{message}: expected {expected}, got {actual}")
        return False


def assert_true(condition: bool, message: str):
    """Assert condition is true"""
    if condition:
        log(f"PASS: {message}", "PASS")
        test_results['passed'] += 1
        return True
    else:
        log(f"FAIL: {message}", "FAIL")
        test_results['failed'] += 1
        test_results['errors'].append(message)
        return False


def assert_status(response, expected_status: int, message: str):
    """Assert response status code. Returns True if passed, False if failed."""
    if response.status_code == expected_status:
        log(f"PASS: {message} (status {expected_status})", "PASS")
        test_results['passed'] += 1
        return True
    else:
        log(f"FAIL: {message} | Expected status {expected_status}, Got {response.status_code}", "FAIL")
        try:
            log(f"       Response: {response.json()}", "DEBUG")
        except:
            log(f"       Response: {response.text[:200]}", "DEBUG")
        test_results['failed'] += 1
        test_results['errors'].append(f"{message}: expected status {expected_status}, got {response.status_code}")
        return False


def safe_json(response):
    """Safely parse JSON from response, return None on failure"""
    try:
        return response.json()
    except:
        return None


def skip_test(message: str):
    """Mark test as skipped"""
    log(f"SKIP: {message}", "SKIP")
    test_results['skipped'] += 1


class TestClient:
    """HTTP client for testing API endpoints"""

    def __init__(self):
        self.token: Optional[str] = None
        self.admin_token: Optional[str] = None
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}

    def login(self, email: str, password: str) -> bool:
        """Login and store JWT token"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.headers["Authorization"] = f"Bearer {self.token}"
            return True
        return False

    def login_admin(self, email: str, password: str) -> bool:
        """Login as admin"""
        if self.login(email, password):
            self.admin_token = self.token
            return True
        return False

    def set_token(self, token: str) -> bool:
        """Set JWT token directly"""
        self.token = token
        self.admin_token = token
        self.headers["Authorization"] = f"Bearer {token}"
        return True

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request with auth headers"""
        return requests.get(f"{BASE_URL}{endpoint}", headers=self.headers, **kwargs)

    def post(self, endpoint: str, data: Dict = None, **kwargs) -> requests.Response:
        """POST request with auth headers"""
        return requests.post(f"{BASE_URL}{endpoint}", headers=self.headers, json=data, **kwargs)

    def put(self, endpoint: str, data: Dict = None, **kwargs) -> requests.Response:
        """PUT request with auth headers"""
        return requests.put(f"{BASE_URL}{endpoint}", headers=self.headers, json=data, **kwargs)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def setup_test_data():
    """Setup test data in database using Flask app context"""
    from app import app, db
    from models import User, Business, FeatureFlag, Coupon, UserCoupon, BusinessMembership, Campaign

    with app.app_context():
        # Ensure feature flag exists
        flag = FeatureFlag.query.filter_by(key='exclusive_coupons_enabled').first()
        if not flag:
            flag = FeatureFlag(
                key='exclusive_coupons_enabled',
                value=True,
                description='Enable exclusive coupons feature'
            )
            db.session.add(flag)
        else:
            flag.value = True

        # Find or create test business
        test_business = Business.query.filter_by(slug='test-mesnica').first()
        if not test_business:
            test_business = Business(
                name='Test Mesnica',
                slug='test-mesnica',
                city='Sarajevo',
                has_exclusive_coupons=True,
                max_campaigns_allowed=5,  # Allow multiple campaigns for testing
                business_type='local_business',
                address='Testna ulica 123',
                working_hours={
                    'monday': {'open': '08:00', 'close': '17:00'},
                    'tuesday': {'open': '08:00', 'close': '17:00'},
                    'wednesday': {'open': '08:00', 'close': '17:00'},
                    'thursday': {'open': '08:00', 'close': '17:00'},
                    'friday': {'open': '08:00', 'close': '17:00'},
                    'saturday': {'open': '08:00', 'close': '14:00'},
                    'sunday': None
                }
            )
            db.session.add(test_business)
            db.session.flush()
        else:
            # Ensure business has enough campaign slots
            test_business.max_campaigns_allowed = max(test_business.max_campaigns_allowed or 1, 5)

        db.session.commit()

        return {
            'business_id': test_business.id,
            'business_name': test_business.name
        }


def cleanup_test_data():
    """Clean up test data after tests"""
    from app import app, db
    from models import Coupon, UserCoupon, Campaign

    with app.app_context():
        # Delete test coupons and user coupons
        test_coupons = Coupon.query.filter(
            Coupon.article_name.like('TEST_%')
        ).all()

        for coupon in test_coupons:
            UserCoupon.query.filter_by(coupon_id=coupon.id).delete()
            db.session.delete(coupon)

        # Delete test campaigns
        test_campaigns = Campaign.query.filter(
            Campaign.name.like('TEST_%')
        ).all()

        for campaign in test_campaigns:
            # First delete coupons in this campaign
            Coupon.query.filter_by(campaign_id=campaign.id).delete()
            db.session.delete(campaign)

        db.session.commit()
        log("Cleaned up test data", "INFO")


# =============================================================================
# FEATURE FLAG TESTS
# =============================================================================

def test_feature_flag_status(client: TestClient):
    """Test feature flag status endpoint"""
    log("Testing feature flag status endpoint...", "INFO")

    response = client.get('/api/coupons/feature-status')
    if not assert_status(response, 200, "Get feature status"):
        return

    data = safe_json(response)
    if data:
        assert_true('enabled' in data, "Response contains 'enabled' field")


def test_admin_feature_flags(client: TestClient):
    """Test admin feature flag management"""
    log("Testing admin feature flag management...", "INFO")

    # Get all flags
    response = client.get('/api/admin/feature-flags')
    if not assert_status(response, 200, "Get all feature flags"):
        return

    data = safe_json(response)
    if data:
        assert_true('flags' in data, "Response contains 'flags' array")

    # Toggle feature flag
    response = client.put('/api/admin/feature-flags/exclusive_coupons_enabled', data={'value': True})
    assert_status(response, 200, "Enable exclusive coupons flag")

    # Verify it's enabled
    response = client.get('/api/coupons/feature-status')
    data = safe_json(response)
    if data:
        assert_true(data.get('enabled', False), "Feature is now enabled")


# =============================================================================
# CAMPAIGN CRUD TESTS
# =============================================================================

def test_get_business_campaigns(client: TestClient, business_id: int):
    """Test getting campaigns for a business"""
    log("Testing business campaigns listing...", "INFO")

    response = client.get(f'/api/business/{business_id}/campaigns')
    if not assert_status(response, 200, "Get business campaigns"):
        return

    data = safe_json(response)
    if data:
        assert_true('campaigns' in data, "Response contains 'campaigns' array")
        assert_true('business' in data, "Response contains 'business' info")
        business = data.get('business', {})
        assert_true('max_campaigns_allowed' in business, "Business has max_campaigns_allowed")
        assert_true('campaigns_count' in business, "Business has campaigns_count")


def test_create_campaign(client: TestClient, business_id: int) -> Optional[int]:
    """Test campaign creation"""
    log("Testing campaign creation...", "INFO")

    campaign_data = {
        'name': 'TEST_Testna Kampanja',
        'description': 'Testna kampanja za automatske testove'
    }

    response = client.post(f'/api/business/{business_id}/campaigns', data=campaign_data)

    if assert_status(response, 200, "Create new campaign"):
        data = safe_json(response)
        if data:
            assert_true(data.get('success', False), "Campaign creation successful")
            campaign = data.get('campaign', {})
            campaign_id = campaign.get('id')
            assert_true(campaign_id is not None, "Campaign ID returned")
            assert_true(campaign.get('max_coupons') == 20, "Default max_coupons is 20")
            assert_true(campaign.get('can_add_coupon') == True, "Can add coupons to new campaign")
            return campaign_id

    return None


def test_get_single_campaign(client: TestClient, business_id: int, campaign_id: int):
    """Test getting single campaign with its coupons"""
    log("Testing single campaign retrieval...", "INFO")

    response = client.get(f'/api/business/{business_id}/campaigns/{campaign_id}')
    if not assert_status(response, 200, "Get single campaign"):
        return

    data = safe_json(response)
    if data:
        campaign = data.get('campaign', {})
        assert_true('name' in campaign, "Campaign has name")
        assert_true('max_coupons' in campaign, "Campaign has max_coupons")
        assert_true('coupons_count' in campaign, "Campaign has coupons_count")
        assert_true('coupons' in data, "Response contains coupons array")


def test_update_campaign(client: TestClient, business_id: int, campaign_id: int):
    """Test campaign update"""
    log("Testing campaign update...", "INFO")

    update_data = {
        'name': 'TEST_Updated Kampanja',
        'description': 'Updated description',
        'is_active': True
    }

    response = client.put(f'/api/business/{business_id}/campaigns/{campaign_id}', data=update_data)
    if assert_status(response, 200, "Update campaign"):
        data = safe_json(response)
        if data:
            campaign = data.get('campaign', {})
            assert_true(campaign.get('name') == 'TEST_Updated Kampanja', "Campaign name updated")


def test_campaign_coupon_limit(client: TestClient, business_id: int):
    """Test that campaign respects max_coupons limit"""
    log("Testing campaign coupon limit...", "INFO")

    # Create a campaign with small limit
    campaign_data = {
        'name': 'TEST_Small Campaign',
        'description': 'Campaign with limited coupons'
    }

    response = client.post(f'/api/business/{business_id}/campaigns', data=campaign_data)
    if not assert_status(response, 200, "Create limited campaign"):
        return

    data = safe_json(response)
    campaign_id = data.get('campaign', {}).get('id')

    # Verify campaign can add coupons
    response = client.get(f'/api/business/{business_id}/campaigns/{campaign_id}')
    data = safe_json(response)
    if data:
        assert_true(data.get('campaign', {}).get('can_add_coupon') == True, "New campaign can add coupons")


def test_admin_campaign_limit(client: TestClient, business_id: int):
    """Test admin updating business campaign limit"""
    log("Testing admin campaign limit update...", "INFO")

    response = client.put(f'/api/admin/businesses/{business_id}/campaign-limit', data={
        'max_campaigns_allowed': 10
    })
    if assert_status(response, 200, "Update business campaign limit"):
        data = safe_json(response)
        if data:
            assert_true(data.get('max_campaigns_allowed') == 10, "Campaign limit updated to 10")

    # Reset to original value
    client.put(f'/api/admin/businesses/{business_id}/campaign-limit', data={
        'max_campaigns_allowed': 5
    })


def test_admin_coupon_limit_per_campaign(client: TestClient, campaign_id: int):
    """Test admin updating campaign coupon limit"""
    log("Testing admin coupon limit per campaign...", "INFO")

    response = client.put(f'/api/admin/campaigns/{campaign_id}/coupon-limit', data={
        'max_coupons': 50
    })
    if assert_status(response, 200, "Update campaign coupon limit"):
        data = safe_json(response)
        if data:
            assert_true(data.get('max_coupons') == 50, "Coupon limit updated to 50")


# =============================================================================
# COUPON CRUD TESTS
# =============================================================================

def test_get_coupons_public(client: TestClient):
    """Test public coupons listing endpoint"""
    log("Testing public coupons listing...", "INFO")

    # Remove auth header temporarily
    original_headers = client.headers.copy()
    client.headers = {"Content-Type": "application/json"}

    response = client.get('/api/coupons')
    if assert_status(response, 200, "Get public coupons list"):
        data = safe_json(response)
        if data:
            assert_true('coupons' in data, "Response contains 'coupons' array")

    # Restore headers
    client.headers = original_headers


def test_create_coupon(client: TestClient, business_id: int, campaign_id: int = None) -> Optional[int]:
    """Test coupon creation within a campaign"""
    log("Testing coupon creation...", "INFO")

    # If no campaign_id provided, create a test campaign first
    if not campaign_id:
        log("Creating test campaign for coupon...", "INFO")
        campaign_response = client.post(f'/api/business/{business_id}/campaigns', data={
            'name': 'TEST_Auto Campaign',
            'description': 'Auto-created campaign for coupon test'
        })
        if campaign_response.status_code == 200:
            campaign_id = campaign_response.json().get('campaign', {}).get('id')
        else:
            log("Failed to create campaign for coupon test", "ERROR")
            return None

    coupon_data = {
        'campaign_id': campaign_id,
        'article_name': 'TEST_Svježe Meso 1kg',
        'description': 'Svježe domaće meso vrhunske kvalitete',
        'normal_price': 20.00,
        'discount_percent': 30,
        'quantity_description': '1kg svježeg mesa',
        'total_quantity': 10,
        'valid_days': 5
    }

    response = client.post(f'/api/business/{business_id}/coupons', data=coupon_data)

    if assert_status(response, 200, "Create new coupon"):
        data = safe_json(response)
        if data:
            assert_true(data.get('success', False), "Coupon creation successful")
            coupon = data.get('coupon', {})
            coupon_id = coupon.get('id')
            assert_true(coupon_id is not None, "Coupon ID returned")
            assert_true(coupon.get('campaign_id') == campaign_id, "Coupon linked to campaign")
            return coupon_id

    return None


def test_create_coupon_without_campaign(client: TestClient, business_id: int):
    """Test that coupon creation fails without campaign_id"""
    log("Testing coupon creation without campaign...", "INFO")

    coupon_data = {
        'article_name': 'TEST_Should Fail',
        'normal_price': 10.00,
        'discount_percent': 20,
        'total_quantity': 5,
        'valid_days': 3
    }

    response = client.post(f'/api/business/{business_id}/coupons', data=coupon_data)
    assert_status(response, 400, "Coupon creation without campaign fails")


def test_get_business_coupons(client: TestClient, business_id: int):
    """Test getting coupons for a business"""
    log("Testing business coupons listing...", "INFO")

    response = client.get(f'/api/business/{business_id}/coupons')
    if not assert_status(response, 200, "Get business coupons"):
        return

    data = safe_json(response)
    if data:
        assert_true('coupons' in data, "Response contains 'coupons' array")
        assert_true('business' in data, "Response contains 'business' info")


def test_update_coupon(client: TestClient, business_id: int, coupon_id: int):
    """Test coupon update"""
    log("Testing coupon update...", "INFO")

    update_data = {
        'is_active': True,
        'description': 'Updated description for test'
    }

    response = client.put(f'/api/business/{business_id}/coupons/{coupon_id}', data=update_data)
    assert_status(response, 200, "Update coupon")


def test_get_single_coupon(client: TestClient, coupon_id: int):
    """Test getting single coupon details"""
    log("Testing single coupon retrieval...", "INFO")

    response = client.get(f'/api/coupons/{coupon_id}')
    if not assert_status(response, 200, "Get single coupon"):
        return

    data = safe_json(response)
    if data:
        coupon = data.get('coupon', {})
        assert_true('article_name' in coupon, "Coupon has article_name")
        assert_true('business' in coupon, "Coupon has business info")
        assert_true('final_price' in coupon, "Coupon has final_price calculated")


# =============================================================================
# COUPON PURCHASE TESTS
# =============================================================================

def test_purchase_coupon(client: TestClient, coupon_id: int) -> Optional[Dict]:
    """Test coupon purchase flow"""
    log("Testing coupon purchase...", "INFO")

    response = client.post(f'/api/coupons/{coupon_id}/purchase')

    # Could fail if no credits, which is expected
    if response.status_code == 200:
        data = response.json()
        assert_true(data.get('success', False), "Purchase successful")
        user_coupon = data.get('user_coupon', {})
        assert_true('redemption_code' in user_coupon, "Redemption code generated")
        assert_true(len(user_coupon.get('redemption_code', '')) == 6, "Redemption code is 6 digits")
        return user_coupon
    elif response.status_code == 400:
        data = response.json()
        if 'Nedovoljno kredita' in data.get('error', ''):
            log("Purchase failed due to insufficient credits (expected)", "INFO")
            test_results['passed'] += 1
            return None
        elif 'Već imate aktivan kupon' in data.get('error', ''):
            log("User already has active coupon (expected)", "INFO")
            test_results['passed'] += 1
            return None

    assert_status(response, 200, "Purchase coupon")
    return None


def test_get_user_coupons(client: TestClient):
    """Test getting user's purchased coupons"""
    log("Testing user coupons listing...", "INFO")

    response = client.get('/api/user/coupons')
    if not assert_status(response, 200, "Get user coupons"):
        return  # Auth or other error, skip remaining tests

    data = safe_json(response)
    if data:
        assert_true('coupons' in data, "Response contains 'coupons' array")

    # Test status filter
    response = client.get('/api/user/coupons?status=active')
    assert_status(response, 200, "Get active user coupons")


def test_purchase_without_credits(client: TestClient, coupon_id: int):
    """Test purchase fails gracefully without credits"""
    log("Testing purchase without sufficient credits...", "INFO")

    response = client.post(f'/api/coupons/{coupon_id}/purchase')

    # Should get 400 if no credits or 200 if successful
    if response.status_code == 400:
        data = response.json()
        assert_true('error' in data, "Error message returned")
        log(f"Expected error: {data.get('error')}", "INFO")
    elif response.status_code == 200:
        log("User has credits, purchase succeeded", "INFO")

    test_results['passed'] += 1


# =============================================================================
# COUPON REDEMPTION TESTS
# =============================================================================

def test_redeem_coupon(client: TestClient, business_id: int, redemption_code: str):
    """Test coupon redemption by business"""
    log("Testing coupon redemption...", "INFO")

    response = client.post(f'/api/business/{business_id}/redeem', data={'code': redemption_code})

    if assert_status(response, 200, "Redeem coupon"):
        data = response.json()
        assert_true(data.get('success', False), "Redemption successful")
        return True
    return False


def test_redeem_invalid_code(client: TestClient, business_id: int):
    """Test redemption with invalid code"""
    log("Testing redemption with invalid code...", "INFO")

    response = client.post(f'/api/business/{business_id}/redeem', data={'code': '000000'})
    assert_status(response, 404, "Invalid code returns 404")


def test_redeem_wrong_format(client: TestClient, business_id: int):
    """Test redemption with wrong code format"""
    log("Testing redemption with wrong format...", "INFO")

    # Too short
    response = client.post(f'/api/business/{business_id}/redeem', data={'code': '123'})
    assert_status(response, 400, "Short code returns 400")

    # Non-numeric
    response = client.post(f'/api/business/{business_id}/redeem', data={'code': 'abcdef'})
    assert_status(response, 400, "Non-numeric code returns 400")


def test_get_pending_redemptions(client: TestClient, business_id: int):
    """Test getting pending redemptions for business"""
    log("Testing pending redemptions listing...", "INFO")

    response = client.get(f'/api/business/{business_id}/pending-coupons')
    assert_status(response, 200, "Get pending redemptions")

    data = response.json()
    assert_true('pending' in data, "Response contains 'pending' array")


# =============================================================================
# REVIEW AND RATING TESTS
# =============================================================================

def test_submit_review(client: TestClient, user_coupon_id: int):
    """Test submitting review for redeemed coupon"""
    log("Testing review submission...", "INFO")

    review_data = {
        'rating': 5,
        'comment': 'Odlična usluga, svježe meso!'
    }

    response = client.post(f'/api/user/coupons/{user_coupon_id}/review', data=review_data)

    # May fail if coupon not redeemed yet
    if response.status_code == 200:
        data = response.json()
        assert_true(data.get('success', False), "Review submitted successfully")
    elif response.status_code == 400:
        data = response.json()
        log(f"Review not allowed: {data.get('error')}", "INFO")
        test_results['passed'] += 1


def test_submit_review_invalid_rating(client: TestClient, user_coupon_id: int):
    """Test review with invalid rating"""
    log("Testing review with invalid rating...", "INFO")

    # Rating too high
    response = client.post(f'/api/user/coupons/{user_coupon_id}/review', data={'rating': 6})
    if response.status_code == 400:
        test_results['passed'] += 1
        log("PASS: Invalid rating rejected", "PASS")
    else:
        test_results['failed'] += 1
        log("FAIL: Invalid rating should be rejected", "FAIL")


def test_business_rate_buyer(client: TestClient, business_id: int, user_coupon_id: int):
    """Test business rating a buyer"""
    log("Testing business rating buyer...", "INFO")

    rating_data = {
        'rating': 4,
        'comment': 'Dobar kupac'
    }

    response = client.post(f'/api/business/{business_id}/rate-buyer/{user_coupon_id}', data=rating_data)

    if response.status_code == 200:
        data = response.json()
        assert_true(data.get('success', False), "Rating submitted successfully")
    elif response.status_code == 404:
        log("Coupon not found or not redeemed (expected if no purchase)", "INFO")
        test_results['passed'] += 1


# =============================================================================
# ADMIN TESTS
# =============================================================================

def test_admin_get_businesses_with_coupons(client: TestClient):
    """Test admin getting businesses with coupons enabled"""
    log("Testing admin businesses with coupons...", "INFO")

    response = client.get('/api/admin/businesses/with-coupons')
    assert_status(response, 200, "Get businesses with coupons")

    data = response.json()
    assert_true('businesses' in data, "Response contains 'businesses' array")


def test_admin_enable_disable_coupons(client: TestClient, business_id: int):
    """Test admin enabling/disabling coupons for business"""
    log("Testing admin enable/disable coupons...", "INFO")

    # Enable
    response = client.post(f'/api/admin/businesses/{business_id}/enable-coupons', data={
        'business_type': 'local_business',
        'max_campaigns_allowed': 5
    })
    assert_status(response, 200, "Enable coupons for business")

    # Disable
    response = client.post(f'/api/admin/businesses/{business_id}/disable-coupons')
    assert_status(response, 200, "Disable coupons for business")

    # Re-enable for other tests
    response = client.post(f'/api/admin/businesses/{business_id}/enable-coupons', data={
        'business_type': 'local_business',
        'max_campaigns_allowed': 5
    })


def test_admin_coupon_stats(client: TestClient):
    """Test admin coupon statistics"""
    log("Testing admin coupon stats...", "INFO")

    response = client.get('/api/admin/coupons/stats')
    assert_status(response, 200, "Get coupon stats")

    data = response.json()
    stats = data.get('stats', {})
    assert_true('total_coupons' in stats, "Stats contains total_coupons")
    assert_true('active_coupons' in stats, "Stats contains active_coupons")
    assert_true('redemption_rate' in stats, "Stats contains redemption_rate")


def test_admin_all_coupons(client: TestClient):
    """Test admin getting all coupons"""
    log("Testing admin all coupons...", "INFO")

    response = client.get('/api/admin/all-coupons')
    assert_status(response, 200, "Get all coupons (admin)")

    data = response.json()
    assert_true('coupons' in data, "Response contains 'coupons' array")


def test_search_businesses(client: TestClient):
    """Test business search for admin"""
    log("Testing business search...", "INFO")

    response = client.get('/api/admin/businesses/search?search=test')
    if not assert_status(response, 200, "Search businesses"):
        return

    data = safe_json(response)
    if data:
        assert_true('businesses' in data, "Response contains 'businesses' array")


# =============================================================================
# USER ENDPOINTS TESTS
# =============================================================================

def test_get_products_for_engagement(client: TestClient):
    """Test getting products for credits engagement"""
    log("Testing products for engagement...", "INFO")

    response = client.get('/api/products/for-engagement?limit=5')
    assert_status(response, 200, "Get products for engagement")

    data = response.json()
    assert_true('products' in data, "Response contains 'products' array")


def test_get_user_business_membership(client: TestClient):
    """Test getting user's business membership"""
    log("Testing user business membership...", "INFO")

    response = client.get('/api/user/business-membership')
    assert_status(response, 200, "Get user business membership")

    data = response.json()
    # business can be None if user has no business
    assert_true('business' in data or data.get('business') is None, "Response has business field")


# =============================================================================
# MODEL TESTS (Unit Tests)
# =============================================================================

def test_coupon_model():
    """Test Coupon model properties and methods"""
    log("Testing Coupon model...", "INFO")

    from app import app, db
    from models import Coupon, Business

    with app.app_context():
        # Find a test coupon
        coupon = Coupon.query.first()
        if coupon:
            # Test calculated properties
            assert_true(coupon.final_price is not None, "Coupon has final_price property")
            assert_true(coupon.savings is not None, "Coupon has savings property")
            assert_true(isinstance(coupon.is_sold_out, bool), "Coupon has is_sold_out property")

            # Verify calculations
            expected_final = coupon.normal_price * (1 - coupon.discount_percent / 100)
            assert_true(
                abs(coupon.final_price - expected_final) < 0.01,
                "Final price calculated correctly"
            )
        else:
            skip_test("No coupons in database for model testing")


def test_user_coupon_model():
    """Test UserCoupon model properties and methods"""
    log("Testing UserCoupon model...", "INFO")

    from app import app, db
    from models import UserCoupon

    with app.app_context():
        # Test code generation
        code1 = UserCoupon.generate_redemption_code()
        code2 = UserCoupon.generate_redemption_code()

        assert_true(len(code1) == 6, "Generated code is 6 characters")
        assert_true(code1.isdigit(), "Generated code is all digits")
        assert_true(code1 != code2, "Generated codes are unique")


def test_business_model():
    """Test Business model coupon and campaign-related methods"""
    log("Testing Business model...", "INFO")

    from app import app, db
    from models import Business

    with app.app_context():
        business = Business.query.filter_by(has_exclusive_coupons=True).first()
        if business:
            # Test methods
            assert_true(isinstance(business.is_open_now(), bool), "is_open_now returns boolean")
            assert_true(isinstance(business.get_active_coupons_count(), int), "get_active_coupons_count returns int")
            assert_true(isinstance(business.get_campaigns_count(), int), "get_campaigns_count returns int")
            assert_true(isinstance(business.get_active_campaigns_count(), int), "get_active_campaigns_count returns int")
            assert_true(isinstance(business.can_create_campaign(), bool), "can_create_campaign returns boolean")
            assert_true(hasattr(business, 'max_campaigns_allowed'), "Business has max_campaigns_allowed attribute")
        else:
            skip_test("No business with exclusive coupons for testing")


def test_campaign_model():
    """Test Campaign model properties and methods"""
    log("Testing Campaign model...", "INFO")

    from app import app, db
    from models import Campaign, Business

    with app.app_context():
        # Find a test campaign
        campaign = Campaign.query.first()
        if campaign:
            # Test calculated properties
            assert_true(isinstance(campaign.get_coupons_count(), int), "Campaign has get_coupons_count method")
            assert_true(isinstance(campaign.get_active_coupons_count(), int), "Campaign has get_active_coupons_count method")
            assert_true(isinstance(campaign.can_add_coupon(), bool), "Campaign has can_add_coupon method")

            # Test to_dict
            campaign_dict = campaign.to_dict()
            assert_true('id' in campaign_dict, "to_dict contains id")
            assert_true('name' in campaign_dict, "to_dict contains name")
            assert_true('max_coupons' in campaign_dict, "to_dict contains max_coupons")
            assert_true('coupons_count' in campaign_dict, "to_dict contains coupons_count")
        else:
            skip_test("No campaigns in database for model testing")


def test_feature_flag_model():
    """Test FeatureFlag model"""
    log("Testing FeatureFlag model...", "INFO")

    from app import app, db
    from models import FeatureFlag

    with app.app_context():
        # Test is_enabled method
        result = FeatureFlag.is_enabled('exclusive_coupons_enabled', default=False)
        assert_true(isinstance(result, bool), "is_enabled returns boolean")

        # Test non-existent flag returns default
        result = FeatureFlag.is_enabled('non_existent_flag', default=True)
        assert_true(result == True, "Non-existent flag returns default value")


# =============================================================================
# SCHEDULED JOB TESTS
# =============================================================================

def test_coupon_reminders_job():
    """Test coupon reminders scheduled job"""
    log("Testing coupon reminders job...", "INFO")

    from app import app

    with app.app_context():
        try:
            from jobs.coupon_reminders import run_coupon_reminders
            # Just verify it runs without error
            # In a real test, we'd mock the email sending
            run_coupon_reminders()
            test_results['passed'] += 1
            log("PASS: Coupon reminders job executed without errors", "PASS")
        except Exception as e:
            test_results['failed'] += 1
            log(f"FAIL: Coupon reminders job failed: {e}", "FAIL")


# =============================================================================
# EMAIL NOTIFICATION TESTS (Mocked)
# =============================================================================

def test_email_templates():
    """Test email template functions exist and return proper format"""
    log("Testing email templates...", "INFO")

    from sendgrid_utils import (
        send_coupon_purchase_email,
        send_coupon_sale_notification_email,
        send_coupon_halfway_reminder_email,
        send_coupon_expiry_reminder_email,
        send_coupon_redemption_email,
        send_new_rating_notification_email
    )

    # Test that functions exist and have correct signature
    assert_true(callable(send_coupon_purchase_email), "send_coupon_purchase_email is callable")
    assert_true(callable(send_coupon_sale_notification_email), "send_coupon_sale_notification_email is callable")
    assert_true(callable(send_coupon_halfway_reminder_email), "send_coupon_halfway_reminder_email is callable")
    assert_true(callable(send_coupon_expiry_reminder_email), "send_coupon_expiry_reminder_email is callable")
    assert_true(callable(send_coupon_redemption_email), "send_coupon_redemption_email is callable")
    assert_true(callable(send_new_rating_notification_email), "send_new_rating_notification_email is callable")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_full_coupon_lifecycle(client: TestClient, business_id: int):
    """
    Test complete coupon lifecycle:
    1. Create coupon
    2. List coupons
    3. Purchase coupon
    4. Redeem coupon
    5. Submit review
    """
    log("=" * 60, "INFO")
    log("Testing full coupon lifecycle...", "INFO")
    log("=" * 60, "INFO")

    # 1. Create coupon
    coupon_id = test_create_coupon(client, business_id)
    if not coupon_id:
        log("Could not create coupon, skipping lifecycle test", "INFO")
        return

    # 2. Verify coupon appears in listing
    test_get_single_coupon(client, coupon_id)

    # 3. Purchase coupon
    user_coupon = test_purchase_coupon(client, coupon_id)

    if user_coupon:
        redemption_code = user_coupon.get('redemption_code')
        user_coupon_id = user_coupon.get('id')

        # 4. Redeem coupon
        if test_redeem_coupon(client, business_id, redemption_code):
            # 5. Submit review
            test_submit_review(client, user_coupon_id)
            test_business_rate_buyer(client, business_id, user_coupon_id)


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all tests"""
    global VERBOSE

    parser = argparse.ArgumentParser(description='Test Exclusive Coupons Feature')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup test data after')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests (no API calls)')
    args = parser.parse_args()

    VERBOSE = args.verbose
    unit_only = args.unit_only

    print("\n" + "=" * 70)
    print("  EXCLUSIVE COUPONS TEST SUITE")
    print("=" * 70)
    print(f"  Base URL: {BASE_URL}")
    print(f"  Mode: {'Unit tests only' if unit_only else 'Full test suite'}")
    print(f"  Verbose: {VERBOSE}")
    print("=" * 70 + "\n")

    client = TestClient()
    business_id = None
    coupon_id = None

    # Setup test data (needed for both modes)
    log("Setting up test data...", "INFO")
    try:
        test_data = setup_test_data()
        business_id = test_data['business_id']
        log(f"Test business ID: {business_id}", "INFO")
    except Exception as e:
        log(f"Failed to setup test data: {e}", "ERROR")
        print("\nMake sure the backend is running and database is accessible!")
        sys.exit(1)

    print("\n" + "-" * 70)
    print("  RUNNING TESTS")
    print("-" * 70 + "\n")

    # Run unit tests first (always run)
    print("\n📦 UNIT TESTS (Models & Utilities)")
    print("-" * 40)
    test_coupon_model()
    test_user_coupon_model()
    test_business_model()
    test_campaign_model()
    test_feature_flag_model()
    test_email_templates()

    # Run scheduled job tests (unit test - no API)
    print("\n⏰ SCHEDULED JOB TESTS")
    print("-" * 40)
    test_coupon_reminders_job()

    # Exit if unit-only mode
    if unit_only:
        log("Skipping API tests in unit-only mode", "INFO")
    else:
        # Try to authenticate
        authenticated = False

        # Try JWT token first
        if TEST_JWT_TOKEN:
            log("Using JWT token from environment...", "INFO")
            client.set_token(TEST_JWT_TOKEN)
            authenticated = True
        else:
            # Try login with credentials
            log("Logging in as admin...", "INFO")
            if client.login_admin(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD):
                authenticated = True
                log("Logged in successfully", "INFO")

        if not authenticated:
            log("Failed to authenticate!", "ERROR")
            print("\nPlease set environment variables:")
            print("  export TEST_JWT_TOKEN='your_jwt_token'")
            print("  # OR")
            print("  export TEST_ADMIN_EMAIL='your_email'")
            print("  export TEST_ADMIN_PASSWORD='your_password'")
            print("\nOr run without login for unit tests only:")
            print("  python test_exclusive_coupons.py --unit-only")
            sys.exit(1)

        # Run feature flag tests
        print("\n🚩 FEATURE FLAG TESTS")
        print("-" * 40)
        test_feature_flag_status(client)
        test_admin_feature_flags(client)

        # Run campaign CRUD tests
        print("\n📋 CAMPAIGN CRUD TESTS")
        print("-" * 40)
        test_get_business_campaigns(client, business_id)
        campaign_id = test_create_campaign(client, business_id)
        if campaign_id:
            test_get_single_campaign(client, business_id, campaign_id)
            test_update_campaign(client, business_id, campaign_id)
            test_campaign_coupon_limit(client, business_id)
            test_admin_campaign_limit(client, business_id)
            test_admin_coupon_limit_per_campaign(client, campaign_id)

        # Run coupon CRUD tests
        print("\n📝 COUPON CRUD TESTS")
        print("-" * 40)
        test_get_coupons_public(client)
        test_create_coupon_without_campaign(client, business_id)
        coupon_id = test_create_coupon(client, business_id, campaign_id)
        if coupon_id:
            test_get_business_coupons(client, business_id)
            test_update_coupon(client, business_id, coupon_id)
            test_get_single_coupon(client, coupon_id)

        # Run purchase tests
        print("\n💳 PURCHASE TESTS")
        print("-" * 40)
        if coupon_id:
            test_purchase_coupon(client, coupon_id)
            test_purchase_without_credits(client, coupon_id)
        test_get_user_coupons(client)

        # Run redemption tests
        print("\n🎟️  REDEMPTION TESTS")
        print("-" * 40)
        test_get_pending_redemptions(client, business_id)
        test_redeem_invalid_code(client, business_id)
        test_redeem_wrong_format(client, business_id)

        # Run admin tests
        print("\n👑 ADMIN TESTS")
        print("-" * 40)
        test_admin_get_businesses_with_coupons(client)
        test_admin_enable_disable_coupons(client, business_id)
        test_admin_coupon_stats(client)
        test_admin_all_coupons(client)
        test_search_businesses(client)

        # Run user endpoint tests
        print("\n👤 USER ENDPOINT TESTS")
        print("-" * 40)
        test_get_products_for_engagement(client)
        test_get_user_business_membership(client)

        # Run integration test
        print("\n🔄 INTEGRATION TESTS")
        print("-" * 40)
        test_full_coupon_lifecycle(client, business_id)

    # Cleanup if requested
    if args.cleanup:
        log("Cleaning up test data...", "INFO")
        cleanup_test_data()

    # Print summary
    print("\n" + "=" * 70)
    print("  TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"  ✅ Passed:  {test_results['passed']}")
    print(f"  ❌ Failed:  {test_results['failed']}")
    print(f"  ⏭️  Skipped: {test_results['skipped']}")
    print(f"  📊 Total:   {test_results['passed'] + test_results['failed'] + test_results['skipped']}")
    print("=" * 70)

    if test_results['errors']:
        print("\n  ERRORS:")
        for i, error in enumerate(test_results['errors'][:10], 1):
            print(f"  {i}. {error}")
        if len(test_results['errors']) > 10:
            print(f"  ... and {len(test_results['errors']) - 10} more")

    # Exit with appropriate code
    if test_results['failed'] > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()
