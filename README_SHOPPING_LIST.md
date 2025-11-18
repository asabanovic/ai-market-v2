# AI Pijaca - Shopping List & Favorites Feature

**Implementation Date:** November 12, 2025
**Version:** 1.0.0

This document describes the 24-hour Shopping List and Favorites features added to AI Pijaca.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Backend Implementation](#backend-implementation)
- [Frontend Implementation](#frontend-implementation)
- [Setup Instructions](#setup-instructions)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What's New

1. **24-Hour Shopping List**: Users can build a shopping cart that expires after 24 hours. Items cost 1 credit to add, and checkout is FREE (promo). The list shows grouped receipts by store with savings calculations.

2. **Favorites**: Users can bookmark products for quick access. First add costs 1 credit, subsequent adds of the same product are idempotent (no charge).

3. **SMS Receipts**: On checkout, users receive an SMS with their shopping list grouped by store.

4. **Credit System**: Track user credit balance with transaction ledger for all actions.

### Key Constraints

- **Max 10 distinct items** per active shopping list (quantity increases don't count toward limit)
- **24-hour TTL** for shopping lists
- **1 credit** to add item or favorite
- **0 credits** for checkout (promotional pricing)

---

## Features

### 1. Favorites

- **Add to favorites**: Costs 1 credit on first add, idempotent thereafter
- **View favorites**: List all favorited products with details
- **Remove favorites**: No credit refund
- **Heart icon** on product cards with badge count in header

### 2. Shopping List

- **Add items**: Select product and store (offer_id), specify quantity
- **10-item limit**: Enforced on distinct (product_id, offer_id) pairs
- **Quantity management**: Increment/decrement with stepper controls
- **24-hour expiry**: Automatic expiration via scheduled job
- **TTL countdown**: Real-time countdown in header (mm:ss or hh:mm:ss)
- **Grouped receipt**: Items grouped by store with subtotals and savings

### 3. Checkout

- **Free checkout**: 0 credits (promo: original 5 credits → 0)
- **SMS notification**: Receipt sent to user's phone number
- **Phone capture**: Prompts user if phone not on profile
- **Status tracking**: Lists marked as SENT after checkout

### 4. Credit System

- **Transaction ledger**: All credit changes logged
- **Insufficient credits**: 402 error with user-friendly toast
- **Balance tracking**: Header shows remaining credits

---

## Backend Implementation

### Database Models

Located in: `backend/models.py`

#### CreditTransaction
```python
- id (PK)
- user_id (FK)
- delta (INT) - positive/negative
- balance_after (INT)
- action (STRING) - 'ADD_TO_CART', 'ADD_FAVORITE', 'CHECKOUT_SMS', etc.
- transaction_metadata (JSON)
- created_at
```

#### Favorite
```python
- id (PK)
- user_id (FK)
- product_id (FK)
- created_at
- Unique: (user_id, product_id)
```

#### ShoppingList
```python
- id (PK)
- user_id (FK)
- status (ENUM: ACTIVE, EXPIRED, SENT, CANCELLED)
- created_at
- expires_at (created_at + 24h)
- sent_at (nullable)
```

#### ShoppingListItem
```python
- id (PK)
- list_id (FK)
- product_id (FK)
- business_id (FK) - store-specific offer
- qty (INT)
- price_snapshot (FLOAT)
- old_price_snapshot (FLOAT, nullable)
- discount_percent_snapshot (INT, nullable)
- created_at, updated_at
- Unique: (list_id, product_id, business_id)
```

#### SMSOutbox
```python
- id (PK)
- user_id (FK)
- list_id (FK, nullable)
- phone (STRING)
- body (TEXT)
- status (ENUM: QUEUED, SENT, FAILED)
- provider_message_id (STRING, nullable)
- error_message (TEXT, nullable)
- created_at, sent_at (nullable)
```

### Services

#### CreditsService (`backend/credits_service.py`)

```python
- get_balance(user_id) -> int
- deduct_credits(user_id, amount, action, metadata) -> dict
- add_credits(user_id, amount, action, metadata) -> dict
- has_sufficient_credits(user_id, amount) -> bool
- record_free_transaction(user_id, action, metadata) -> dict
- get_transaction_history(user_id, limit) -> list
- initialize_user_credits(user_id, initial_amount) -> dict
```

**Raises:**
- `InsufficientCreditsError(credits_needed, credits_available)`

#### SMSService (`backend/sms_service.py`)

```python
- queue_sms(user_id, phone, body, list_id) -> dict
- send_sms_now(user_id, phone, body, list_id) -> dict
- process_queued_messages(limit) -> dict
- format_receipt_sms(receipt_data) -> str
- validate_phone_number(phone) -> (is_valid, formatted, error_msg)
```

**Requirements:**
- Environment variables: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### API Endpoints

Blueprint: `shopping_api_bp` in `backend/shopping_api.py`

All endpoints require JWT authentication via `@require_jwt_auth` decorator.

#### Favorites

```
POST   /api/favorites              - Add favorite (1 credit, idempotent)
GET    /api/favorites              - Get user's favorites
DELETE /api/favorites/{id}         - Remove favorite
```

#### Shopping List

```
POST   /api/shopping-list/items                - Add item (1 credit)
PATCH  /api/shopping-list/items/{id}           - Update quantity
DELETE /api/shopping-list/items/{id}           - Remove item
GET    /api/shopping-list/header/ttl           - Get TTL and item count
GET    /api/shopping-list/sidebar              - Get full list with groups
POST   /api/shopping-list/{list_id}/checkout   - Checkout (0 credits)
```

### Scheduled Jobs

#### Expire Lists Job (`backend/jobs/expire_lists.py`)

Runs every 10 minutes to expire shopping lists:

```python
UPDATE shopping_lists
SET status='EXPIRED'
WHERE status='ACTIVE' AND expires_at < NOW()
```

**Setup with cron:**
```bash
*/10 * * * * cd /path/to/backend && python3 jobs/expire_lists.py >> logs/expire_lists.log 2>&1
```

### Migrations

**Alembic Migration:** `backend/alembic/versions/e620e8e8e940_add_shopping_list_and_favorites_tables.py`

Adds:
- `credit_transactions` table with user_id index
- `favorites` table with unique constraint and indexes
- `shopping_lists` table with status/expiry indexes
- `shopping_list_items` table with unique constraint
- `sms_outbox` table with status/date indexes
- `phone` column to `users` table

**Run migration:**
```bash
cd backend
alembic upgrade head
```

---

## Frontend Implementation

### Pinia Stores

Located in: `frontend/stores/`

#### useCartStore (`stores/cart.ts`)

**State:**
```typescript
- listId: number | null
- ttlSeconds: number | null
- itemCount: number
- sidebar: SidebarData | null
- loading: boolean
```

**Getters:**
```typescript
- isActive: computed(() => ttlSeconds > 0)
- ttlFormatted: computed(() => "mm:ss" or "hh:mm:ss")
```

**Actions:**
```typescript
- fetchHeader() - Get TTL and item count
- fetchSidebar() - Get full list with groups
- addItem(productId, offerId, qty) - Add item
- updateQty(itemId, qty) - Update quantity
- removeItem(itemId) - Remove item
- checkout(phone?) - Checkout list
- startTtlTicker() - Start countdown
- stopTtlTicker() - Stop countdown
- reset() - Clear state
```

#### useFavoritesStore (`stores/favorites.ts`)

**State:**
```typescript
- items: FavoriteSummary[]
- loading: boolean
```

**Getters:**
```typescript
- count: computed(() => items.length)
- isFavorited: (productId) => boolean
- getFavoriteId: (productId) => number | null
```

**Actions:**
```typescript
- fetchFavorites() - Get user's favorites
- addFavorite(productId) - Add favorite
- removeFavorite(favoriteId) - Remove favorite
- toggleFavorite(productId) - Toggle favorite
- reset() - Clear state
```

### Composables

#### useCreditsToast (`composables/useCreditsToast.ts`)

Global toast notification system for credits and errors.

**Methods:**
```typescript
- showToast(toast) - Show custom toast
- dismissToast(id) - Dismiss toast
- handleInsufficientCredits(error) - Handle 402 errors
- handleListItemLimit() - Handle 10-item limit
- handleApiError(error) - Handle any API error
- showSuccess(message, title?) - Success toast
- showInfo(message, title?) - Info toast
- showWarning(message, title?) - Warning toast
- showError(message, title?) - Error toast
- clearAll() - Clear all toasts
```

### Components

#### HeaderIcons.vue

Shows favorites heart and shopping cart icons with badges.

**Features:**
- Heart icon with count badge
- Cart icon with count badge and TTL countdown
- Fetches data on mount
- Starts TTL ticker if cart is active
- Emits `toggle-sidebar` event

#### ShoppingSidebar.vue

Full-screen sidebar with shopping list receipt.

**Features:**
- Grouped by store
- Item quantity steppers
- Real-time subtotals and savings
- Phone number capture
- Checkout button with promo pricing display
- Auto-refresh every 30s while open
- TTL countdown in header

**Props:**
```typescript
- isOpen: boolean
```

**Events:**
```typescript
- close: void
```

#### FavoriteButton.vue

Heart button for product cards.

**Features:**
- Toggles favorite state
- Filled/outline heart icon
- Loading animation
- Handles API errors

**Props:**
```typescript
- productId: number
```

**Events:**
```typescript
- updated: void - Emitted after favorite change
```

#### ToastContainer.vue

Global toast notification container.

**Features:**
- Positioned top-right
- Color-coded by type (info, success, warning, error)
- Icons for each type
- Auto-dismiss after duration
- Optional action button
- Smooth transitions

### Integration

**Header.vue** updated to include:
- `<HeaderIcons />` - Shows heart and cart icons
- `<ShoppingSidebar />` - Renders shopping list sidebar
- `<ToastContainer />` - Renders global toasts

---

## Setup Instructions

### 1. Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run Alembic migration
alembic upgrade head

# Set environment variables in .env
DATABASE_URL=postgresql://user:pass@localhost/db
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+38761234567

# Setup cron job for expiring lists
crontab -e
# Add: */10 * * * * cd /path/to/backend && python3 jobs/expire_lists.py >> logs/expire_lists.log 2>&1
```

### 2. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Run dev server
npm run dev
```

### 3. Initialize User Credits

When a new user registers, initialize their credits:

```python
from credits_service import CreditsService

# Give new user 10 credits
CreditsService.initialize_user_credits(user_id, initial_amount=10)
```

---

## API Reference

### POST /api/favorites

Add product to favorites.

**Auth:** Required
**Cost:** 1 credit (first add only)

**Request:**
```json
{
  "product_id": 123
}
```

**Response (201):**
```json
{
  "ok": true,
  "favorite_id": 456,
  "credits_left": 9
}
```

**Response (200 - already favorited):**
```json
{
  "ok": true,
  "already": true,
  "favorite_id": 456,
  "message": "Proizvod je već u omiljenim"
}
```

**Error (402):**
```json
{
  "code": "INSUFFICIENT_CREDITS",
  "needs_topup": true,
  "credits_left": 0,
  "message": "Nemate dovoljno kredita"
}
```

---

### GET /api/favorites

Get user's favorites.

**Auth:** Required
**Cost:** Free

**Response (200):**
```json
[
  {
    "favorite_id": 456,
    "product_id": 123,
    "name": "Instant kafa 3u1",
    "image_url": "/images/product.jpg",
    "category": "Kafa i čaj",
    "price": 2.95,
    "old_price": 3.95,
    "discount_percent": 25,
    "business": {
      "id": 1,
      "name": "Bingo",
      "logo": "/logos/bingo.png"
    },
    "created_at": "2025-11-12T10:30:00Z"
  }
]
```

---

### POST /api/shopping-list/items

Add item to shopping list.

**Auth:** Required
**Cost:** 1 credit (per distinct item, not per qty increment)

**Request:**
```json
{
  "product_id": 123,
  "offer_id": 1,
  "qty": 2
}
```

**Response (201 - new item):**
```json
{
  "ok": true,
  "list_id": 789,
  "item_id": 101,
  "ttl_seconds": 86340,
  "credits_left": 8
}
```

**Response (200 - qty increment):**
```json
{
  "ok": true,
  "list_id": 789,
  "item_id": 101,
  "ttl_seconds": 86340,
  "credits_left": 8
}
```

**Error (400 - item limit):**
```json
{
  "code": "LIST_ITEM_LIMIT",
  "limit": 10,
  "message": "Dostigli ste limit od 10 artikala u listi"
}
```

---

### GET /api/shopping-list/sidebar

Get full shopping list with grouped receipt.

**Auth:** Required
**Cost:** Free

**Response (200):**
```json
{
  "list_id": 789,
  "ttl_seconds": 86340,
  "groups": [
    {
      "store": {
        "id": 1,
        "name": "Bingo",
        "logo": "/logos/bingo.png"
      },
      "items": [
        {
          "item_id": 101,
          "product_id": 123,
          "name": "Instant kafa 3u1",
          "qty": 2,
          "unit_price": 2.95,
          "subtotal": 5.90,
          "old_price": 3.95,
          "estimated_saving": 2.00
        }
      ],
      "group_subtotal": 5.90,
      "group_saving": 2.00
    }
  ],
  "total_items": 6,
  "grand_total": 23.40,
  "grand_saving": 7.10
}
```

---

### POST /api/shopping-list/{list_id}/checkout

Checkout shopping list and send SMS.

**Auth:** Required
**Cost:** 0 credits (promo)

**Request:**
```json
{
  "phone": "+38761234567"
}
```

**Response (200):**
```json
{
  "queued": true,
  "checkout_fee_ui": {
    "original": 5,
    "final": 0,
    "promo": true
  },
  "ttl_seconds": 5400,
  "sms_status": "SENT"
}
```

**Error (400 - needs phone):**
```json
{
  "error": "Phone number is required",
  "needs_phone": true
}
```

---

## Testing

### Manual Testing Checklist

#### Favorites
- [ ] Add favorite (verify 1 credit deducted)
- [ ] Add same favorite again (verify no credit charge)
- [ ] View favorites list
- [ ] Remove favorite
- [ ] Badge count updates in header

#### Shopping List
- [ ] Add item to empty list (verify list created with 24h expiry)
- [ ] Add 10 distinct items successfully
- [ ] Try adding 11th distinct item (verify error)
- [ ] Increment qty on existing item (verify no item limit)
- [ ] Decrement qty
- [ ] Remove item
- [ ] View sidebar with grouped receipt
- [ ] Verify TTL countdown updates every second
- [ ] Badge count updates in header

#### Checkout
- [ ] Checkout with phone on profile
- [ ] Checkout without phone (verify phone capture)
- [ ] Verify SMS received with correct format
- [ ] Verify 0 credits charged (promo UI shown)
- [ ] Verify list marked as SENT

#### Credits
- [ ] Insufficient credits shows 402 error toast
- [ ] Toast has "Kupi kredite" CTA button
- [ ] Credit balance updates in real-time

#### Expiration
- [ ] Wait for list to expire (or manually update expires_at in DB)
- [ ] Run expire job: `python3 backend/jobs/expire_lists.py`
- [ ] Verify list status changed to EXPIRED
- [ ] Verify TTL shows 0 in frontend

### Automated Tests

```bash
# Backend tests (to be added)
cd backend
pytest tests/test_credits_service.py
pytest tests/test_shopping_api.py

# Frontend tests (to be added)
cd frontend
npm run test
```

---

## Troubleshooting

### SMS Not Sending

**Check Twilio configuration:**
```bash
# Verify environment variables
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $TWILIO_PHONE_NUMBER
```

**Check SMS outbox table:**
```sql
SELECT * FROM sms_outbox WHERE status = 'FAILED' ORDER BY created_at DESC LIMIT 10;
```

### Credits Not Deducting

**Check transaction log:**
```python
from credits_service import CreditsService
history = CreditsService.get_transaction_history(user_id)
print(history)
```

**Manually add credits:**
```python
CreditsService.add_credits(user_id, 10, 'MANUAL_TOP_UP')
```

### Lists Not Expiring

**Manually run job:**
```bash
cd backend
python3 jobs/expire_lists.py
```

**Check cron is running:**
```bash
crontab -l
# Verify job is scheduled
```

### Frontend Components Not Loading

**Check Pinia installation:**
```bash
cd frontend
npm list @pinia/nuxt
```

**Check browser console:**
```
F12 → Console → Look for errors
```

**Verify stores are imported:**
```typescript
// In any component
import { useCartStore } from '~/stores/cart'
const cartStore = useCartStore()
console.log(cartStore.itemCount)
```

### Database Migration Issues

**Check current revision:**
```bash
cd backend
alembic current
```

**Rollback if needed:**
```bash
alembic downgrade -1
```

**Re-run migration:**
```bash
alembic upgrade head
```

---

## Implementation Notes

### Design Decisions

1. **Why 10-item limit?**
   - Keeps lists focused and encourages completion
   - Prevents spam/abuse
   - Manageable for SMS format

2. **Why 24-hour expiry?**
   - Daily shopping cycle in BiH
   - Encourages timely purchases
   - Aligns with "deals expire daily" model

3. **Why free checkout?**
   - Promotional strategy to encourage usage
   - Revenue comes from premium features later
   - Lowers barrier to trying the feature

4. **Why idempotent favorites?**
   - Better UX (no accidental double-charges)
   - Matches user expectations
   - Reduces support requests

### Pragmatic Choices

1. **Store-specific offers via `business_id`**
   - Same product may have different prices at different stores
   - Allows user to compare and choose best deal

2. **Price snapshots**
   - Capture price at time of add
   - Protects user from price increases
   - Shows accurate savings calculation

3. **SMS via Twilio**
   - Reliable delivery
   - Simple API
   - Can be replaced with other providers if needed

4. **Toast notifications over modals**
   - Less intrusive
   - Allows continued browsing
   - Better mobile UX

---

## Future Enhancements

### Possible Features

1. **Recurring Lists**
   - Save lists as templates
   - One-click re-order

2. **List Sharing**
   - Share list with family/friends via link
   - Collaborative shopping

3. **Price Alerts**
   - Notify when favorited item goes on sale
   - Set price drop thresholds

4. **Shopping History**
   - View past lists
   - Reorder from history

5. **Store Optimization**
   - AI suggests which stores to visit
   - Minimize total cost vs. travel time

6. **Credits Packages**
   - Monthly subscriptions
   - Bulk credit purchases
   - Premium tier with unlimited lists

---

## Contact & Support

For questions or issues:
- **GitHub Issues**: [github.com/anthropics/ai-pijaca/issues](https://github.com)
- **Email**: adnanxteam@gmail.com
- **Documentation**: See README.md for general setup

---

**End of Documentation**
