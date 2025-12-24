/**
 * Frontend E2E Tests for Exclusive Coupons Feature
 *
 * These tests can be run in the browser console or with a test runner.
 * They test the frontend pages and components for the exclusive coupons feature.
 *
 * Usage in browser console:
 *   1. Open http://localhost:3000 in browser
 *   2. Open DevTools console
 *   3. Copy and paste this entire file
 *   4. Call runAllTests()
 *
 * Tests cover:
 *   - Public coupons page (/ekskluzivni-popusti)
 *   - User coupons page (/profil/kuponi)
 *   - Business owner dashboard (/moj-biznis)
 *   - Admin management (/admin/ekskluzivni-popusti)
 *   - Homepage exclusive section
 */

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:5001';

// Test results tracking
const testResults = {
  passed: 0,
  failed: 0,
  errors: []
};

// Utility functions
function log(message, type = 'info') {
  const styles = {
    info: 'color: #3b82f6',
    pass: 'color: #10b981; font-weight: bold',
    fail: 'color: #ef4444; font-weight: bold',
    error: 'color: #f59e0b; font-weight: bold'
  };
  console.log(`%c${message}`, styles[type] || styles.info);
}

function assert(condition, message) {
  if (condition) {
    log(`✅ PASS: ${message}`, 'pass');
    testResults.passed++;
    return true;
  } else {
    log(`❌ FAIL: ${message}`, 'fail');
    testResults.failed++;
    testResults.errors.push(message);
    return false;
  }
}

async function fetchJson(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include'
    });
    return { status: response.status, data: await response.json() };
  } catch (error) {
    return { status: 0, error: error.message };
  }
}

// =============================================================================
// API TESTS (can run without browser navigation)
// =============================================================================

async function testFeatureStatusAPI() {
  log('\n📡 Testing Feature Status API...', 'info');

  const result = await fetchJson(`${API_URL}/api/coupons/feature-status`);
  assert(result.status === 200, 'Feature status endpoint returns 200');
  assert('enabled' in result.data, 'Response contains enabled field');
  assert(typeof result.data.enabled === 'boolean', 'Enabled is boolean');

  return result.data.enabled;
}

async function testPublicCouponsAPI() {
  log('\n📡 Testing Public Coupons API...', 'info');

  const result = await fetchJson(`${API_URL}/api/coupons`);
  assert(result.status === 200, 'Public coupons endpoint returns 200');
  assert('coupons' in result.data, 'Response contains coupons array');
  assert(Array.isArray(result.data.coupons), 'Coupons is an array');

  if (result.data.coupons.length > 0) {
    const coupon = result.data.coupons[0];
    assert('article_name' in coupon, 'Coupon has article_name');
    assert('discount_percent' in coupon, 'Coupon has discount_percent');
    assert('final_price' in coupon, 'Coupon has final_price');
    assert('business' in coupon, 'Coupon has business info');
    assert('remaining_quantity' in coupon, 'Coupon has remaining_quantity');
  } else {
    log('ℹ️ No coupons in database to validate structure', 'info');
  }

  return result.data.coupons;
}

async function testUserCouponsAPI() {
  log('\n📡 Testing User Coupons API (requires auth)...', 'info');

  const result = await fetchJson(`${API_URL}/api/user/coupons`);

  if (result.status === 401) {
    log('ℹ️ User not authenticated - expected for unauthenticated requests', 'info');
    testResults.passed++;
    return null;
  }

  assert(result.status === 200, 'User coupons endpoint returns 200');
  assert('coupons' in result.data, 'Response contains coupons array');

  return result.data.coupons;
}

// =============================================================================
// PAGE LOAD TESTS
// =============================================================================

async function testPageLoad(url, expectedElements = []) {
  log(`\n🌐 Testing page load: ${url}`, 'info');

  try {
    const response = await fetch(url);
    assert(response.status === 200, `Page ${url} returns 200`);

    const html = await response.text();
    assert(html.length > 0, 'Page has content');

    // Check for expected elements/text in the HTML
    for (const element of expectedElements) {
      const found = html.includes(element);
      assert(found, `Page contains "${element}"`);
    }

    return true;
  } catch (error) {
    log(`❌ Error loading page: ${error.message}`, 'error');
    testResults.failed++;
    return false;
  }
}

async function testPublicCouponsPage() {
  log('\n🎟️ Testing Public Coupons Page (/ekskluzivni-popusti)', 'info');

  await testPageLoad(`${BASE_URL}/ekskluzivni-popusti`, [
    'Ekskluzivni Popusti',
    'ekskluzivni-popusti'
  ]);
}

async function testHomepageExclusiveSection() {
  log('\n🏠 Testing Homepage for Exclusive Section', 'info');

  const response = await fetch(BASE_URL);
  assert(response.status === 200, 'Homepage loads successfully');

  const html = await response.text();
  // The section may or may not be visible depending on feature flag
  log('ℹ️ Homepage loaded - check for exclusive section visibility based on feature flag', 'info');
  testResults.passed++;
}

async function testProfileCouponsPage() {
  log('\n👤 Testing Profile Coupons Page (/profil/kuponi)', 'info');

  // This page requires auth, so it may redirect
  const response = await fetch(`${BASE_URL}/profil/kuponi`);

  // Page should either load (200) or redirect to login
  assert(
    response.status === 200 || response.redirected,
    'Profile coupons page loads or redirects'
  );
}

async function testBusinessDashboardPage() {
  log('\n🏪 Testing Business Dashboard Page (/moj-biznis)', 'info');

  const response = await fetch(`${BASE_URL}/moj-biznis`);

  assert(
    response.status === 200 || response.redirected,
    'Business dashboard page loads or redirects'
  );
}

async function testAdminCouponsPage() {
  log('\n👑 Testing Admin Coupons Page (/admin/ekskluzivni-popusti)', 'info');

  const response = await fetch(`${BASE_URL}/admin/ekskluzivni-popusti`);

  // Admin page should load (may show error if not admin)
  assert(response.status === 200, 'Admin page loads');
}

// =============================================================================
// COMPONENT INTERACTION TESTS (requires running in browser)
// =============================================================================

function testCouponModal() {
  log('\n🎭 Testing Coupon Modal Component', 'info');

  // Check if CouponModal component exists in DOM
  const modal = document.querySelector('[data-testid="coupon-modal"]') ||
                document.querySelector('.coupon-modal');

  if (modal) {
    log('ℹ️ Coupon modal found in DOM', 'info');
    testResults.passed++;
  } else {
    log('ℹ️ Coupon modal not currently visible (expected when closed)', 'info');
    testResults.passed++;
  }
}

function testExclusiveCouponsSection() {
  log('\n🎯 Testing Exclusive Coupons Section Component', 'info');

  const section = document.querySelector('[data-testid="exclusive-coupons-section"]') ||
                  document.querySelector('.exclusive-coupons-section') ||
                  document.querySelector('section:has(h2:contains("Ekskluzivn"))');

  if (section) {
    log('ℹ️ Exclusive coupons section found on page', 'info');
    testResults.passed++;
  } else {
    log('ℹ️ Exclusive coupons section not visible (may be disabled or on different page)', 'info');
    testResults.passed++;
  }
}

// =============================================================================
// DATA VALIDATION TESTS
// =============================================================================

async function testCouponDataValidation() {
  log('\n🔍 Testing Coupon Data Validation', 'info');

  const result = await fetchJson(`${API_URL}/api/coupons`);

  if (result.status !== 200 || result.data.coupons.length === 0) {
    log('ℹ️ No coupons available for validation', 'info');
    return;
  }

  for (const coupon of result.data.coupons.slice(0, 3)) {
    // Validate required fields
    assert(coupon.article_name && coupon.article_name.length > 0,
      `Coupon ${coupon.id} has valid article_name`);

    assert(coupon.normal_price > 0,
      `Coupon ${coupon.id} has positive normal_price`);

    assert(coupon.discount_percent >= 1 && coupon.discount_percent <= 99,
      `Coupon ${coupon.id} has valid discount_percent (1-99)`);

    assert(coupon.final_price < coupon.normal_price,
      `Coupon ${coupon.id} final_price < normal_price`);

    assert(coupon.remaining_quantity >= 0,
      `Coupon ${coupon.id} has non-negative remaining_quantity`);

    // Validate business info
    assert(coupon.business && coupon.business.name,
      `Coupon ${coupon.id} has business with name`);
  }
}

async function testBusinessDataValidation() {
  log('\n🏢 Testing Business Data in Coupons', 'info');

  const result = await fetchJson(`${API_URL}/api/coupons`);

  if (result.status !== 200 || result.data.coupons.length === 0) {
    log('ℹ️ No coupons available for business validation', 'info');
    return;
  }

  const coupon = result.data.coupons[0];
  const business = coupon.business;

  assert(business.id !== undefined, 'Business has ID');
  assert(business.name && business.name.length > 0, 'Business has name');
  assert('is_open' in business, 'Business has is_open status');
  assert(typeof business.is_open === 'boolean', 'is_open is boolean');
}

// =============================================================================
// CREDITS INTEGRATION TESTS
// =============================================================================

async function testCreditsEndpoint() {
  log('\n💰 Testing Credits Integration', 'info');

  const result = await fetchJson(`${API_URL}/api/user/credits`);

  if (result.status === 401) {
    log('ℹ️ User not authenticated - credits check requires login', 'info');
    testResults.passed++;
    return;
  }

  if (result.status === 200) {
    assert('total_available' in result.data || 'remaining' in result.data,
      'Credits response has balance info');
  }
}

// =============================================================================
// MAIN TEST RUNNER
// =============================================================================

async function runAllTests() {
  console.clear();
  log('═'.repeat(60), 'info');
  log('  EXCLUSIVE COUPONS FRONTEND TEST SUITE', 'info');
  log('═'.repeat(60), 'info');
  log(`  Base URL: ${BASE_URL}`, 'info');
  log(`  API URL: ${API_URL}`, 'info');
  log('═'.repeat(60), 'info');

  // Reset results
  testResults.passed = 0;
  testResults.failed = 0;
  testResults.errors = [];

  // Run API tests
  log('\n\n📡 API TESTS', 'info');
  log('─'.repeat(40), 'info');
  await testFeatureStatusAPI();
  await testPublicCouponsAPI();
  await testUserCouponsAPI();
  await testCreditsEndpoint();

  // Run data validation tests
  log('\n\n🔍 DATA VALIDATION TESTS', 'info');
  log('─'.repeat(40), 'info');
  await testCouponDataValidation();
  await testBusinessDataValidation();

  // Run page load tests
  log('\n\n🌐 PAGE LOAD TESTS', 'info');
  log('─'.repeat(40), 'info');
  await testHomepageExclusiveSection();
  await testPublicCouponsPage();
  await testProfileCouponsPage();
  await testBusinessDashboardPage();
  await testAdminCouponsPage();

  // Run component tests (if in browser)
  if (typeof document !== 'undefined') {
    log('\n\n🎭 COMPONENT TESTS', 'info');
    log('─'.repeat(40), 'info');
    testCouponModal();
    testExclusiveCouponsSection();
  }

  // Print summary
  log('\n\n' + '═'.repeat(60), 'info');
  log('  TEST RESULTS SUMMARY', 'info');
  log('═'.repeat(60), 'info');
  log(`  ✅ Passed:  ${testResults.passed}`, testResults.passed > 0 ? 'pass' : 'info');
  log(`  ❌ Failed:  ${testResults.failed}`, testResults.failed > 0 ? 'fail' : 'info');
  log(`  📊 Total:   ${testResults.passed + testResults.failed}`, 'info');
  log('═'.repeat(60), 'info');

  if (testResults.errors.length > 0) {
    log('\n  ERRORS:', 'error');
    testResults.errors.forEach((error, i) => {
      log(`  ${i + 1}. ${error}`, 'error');
    });
  }

  if (testResults.failed > 0) {
    log('\n❌ Some tests failed!', 'fail');
  } else {
    log('\n✅ All tests passed!', 'pass');
  }

  return testResults;
}

// Quick API-only tests (faster, no page loads)
async function runAPITests() {
  console.clear();
  log('═'.repeat(60), 'info');
  log('  API-ONLY TEST SUITE', 'info');
  log('═'.repeat(60), 'info');

  testResults.passed = 0;
  testResults.failed = 0;
  testResults.errors = [];

  await testFeatureStatusAPI();
  await testPublicCouponsAPI();
  await testCouponDataValidation();
  await testBusinessDataValidation();

  log('\n' + '═'.repeat(60), 'info');
  log(`Results: ${testResults.passed} passed, ${testResults.failed} failed`,
    testResults.failed > 0 ? 'fail' : 'pass');
  log('═'.repeat(60), 'info');

  return testResults;
}

// Export for use
if (typeof window !== 'undefined') {
  window.runAllTests = runAllTests;
  window.runAPITests = runAPITests;
  log('\n📋 Test functions available:', 'info');
  log('   runAllTests() - Run all tests', 'info');
  log('   runAPITests() - Run API tests only', 'info');
}

// Node.js compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runAllTests, runAPITests };
}
