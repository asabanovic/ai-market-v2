# Popust.ba Credits System - Business Logic

## Overview

The application uses a **two-bucket weekly credit system**:
1. **Regular Credits**: 40 per week (reset every Monday) - never exceed 40
2. **Extra Credits**: Earned through engagement activities - accumulate and never reset

**Deduction Priority**: Extra credits are used first, then regular credits.

---

## Credit Earning

| Action | Credits | Notes |
|--------|---------|-------|
| First Search Bonus | +3 extra | One-time, on first search completion |
| Product Vote (up/down) | +2 extra | First vote only, remove vote = -2 refund |
| Product Comment | +5 extra | 20-1000 chars, first comment per product |
| Referral | +100 extra | When referred user registers |
| Feedback Submission | +5 extra | Min 20 chars, 1 bonus per 40 credits spent |

---

## Credit Spending

| Action | Cost | Notes |
|--------|------|-------|
| Search Query | 1-N credits | N = number of items (comma-separated) |
| Add to Favorites | 1 credit | First add only, no refund on remove |
| Add to Shopping List | 1 credit | First add only, quantity changes free |
| Proizvodi Page (page 2+) | 3 credits | Page 1 is free |
| Checkout SMS | 0 credits | Free (promo) |

---

## Weekly Limits

| User Type | Weekly Credits | Reset |
|-----------|---------------|-------|
| Regular User | 40 | Every Monday |
| Admin | 100,000 | Every Monday |

Environment overrides: `REGULAR_USER_WEEKLY_CREDITS`, `ADMIN_WEEKLY_CREDITS`

---

## Key Database Fields (User Model)

```python
weekly_credits: int = 40              # Regular allocation
weekly_credits_used: int = 0          # Used from regular
weekly_credits_reset_date: date       # Next Monday
extra_credits: int = 0                # Earned (never resets)
lifetime_credits_spent: int = 0       # Total ever spent
first_search_reward_claimed: bool     # One-time bonus flag
feedback_bonuses_claimed: int         # Count of feedback bonuses
referral_code: str                    # Auto-generated
custom_referral_code: str             # User-chosen (one-time change)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/credits_service_weekly.py` | Main credit logic (two-bucket system) |
| `backend/engagement_api.py` | Voting, comments (+2, +5 credits) |
| `backend/shopping_api.py` | Favorites, cart (-1 credit each) |
| `backend/agents_api.py` | Search (-N credits), first search bonus |
| `backend/referral_api.py` | Referral codes (+100 credits) |
| `backend/routes.py` | Feedback API (+5 credits) |

---

## Engagement Incentive Summary

1. **Onboarding**: +3 credits for first search
2. **Daily Engagement**: +2 per vote, +5 per comment
3. **Community Growth**: +100 per referral
4. **Feedback Loop**: +5 per quality feedback (gated by spending)
5. **Weekly Refresh**: 40 regular credits every Monday

---

## Proizvodi Page Credits (Implemented)

**Goal**: Charge credits to browse `/proizvodi` page to encourage engagement.

**Implementation**:
- Cost: 3 credits per page view (after page 1) - page 1 is free for any filter
- When out of credits (< 3):
  - Shows `EarnCreditsPopup` explaining how to earn back
  - Disables category selector, store filter, and sort options
  - Pagination buttons are disabled
  - Warning message appears with link to earn credits
- Backend: `routes.py` `/api/products` endpoint checks credits for page > 1
- Frontend: `EarnCreditsPopup.vue` component shows earning options

**Popup Messaging**:
- Header: "Krediti iskorišteni" with remaining credits count
- Options: Comment (+5 credits), Vote (+2 credits)
- Motivational message encouraging helping others with shopping decisions
- Buttons: "Ostani na stranici 1" or "Zaradi kredite"

---

## Homepage Search Credit Limiting (Implemented)

**Goal**: Limit search results to available credits instead of failing completely.

**Implementation**:
- If user searches for 10 items but has 5 credits, only search for first 5 items
- Deduct credits only for items actually searched
- Response includes `items_limited` count and `limited_message` explaining the limitation
- Backend: `agents_api.py` uses `get_available_credits()` and `parse_query_items()` to limit query
- If user has 0 credits, return 403 error with message to earn credits
