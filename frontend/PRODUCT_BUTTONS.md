# Product Tile Buttons - Feature Summary

## Button Layout on Each Product Card

```
┌─────────────────────────────────────┐
│  💗 HEART        -20% DISCOUNT   │  ← Top layer (absolute positioned)
│  (Top Left)      (Top Right)     │
│                                   │
│                                   │
│         PRODUCT IMAGE             │
│                                   │
│                                   │
└─────────────────────────────────────┘
│  Product Title                    │
│  Price Info                       │
│  Business Name                    │
│                                   │
│  ┌──────────┐  ┌──────────┐     │
│  │  Dodaj   │  │ Detalji  │     │  ← Action buttons
│  │ 🛒+      │  │          │     │
│  └──────────┘  └──────────┘     │
└─────────────────────────────────────┘
```

## 1. ❤️ FAVORITE BUTTON (SAČUVAJ)

**Location:** Top-left corner of product image
**Appearance:**
- White circular button with heart icon
- Semi-transparent background (white/90 with backdrop blur)
- Shadow for better visibility
- Heart outline when NOT favorited (gray)
- Filled red heart when favorited

**Functionality:**
- Click to add product to favorites
- System will notify you when new discounts appear for this product
- Costs 1 credit (first time only)
- Tooltip: "Sačuvaj u omiljene - obavijestićemo vas o novim popustima"

**Visual States:**
- ⚪ Outline heart (gray) = Not in favorites
- 🔴 Filled heart (red) = In favorites
- 🔄 Bouncing animation when loading

---

## 2. 🛒 ADD TO SHOPPING LIST BUTTON

**Location:** Bottom-left of product card
**Label:** "Dodaj" with cart icon 🛒+

**Appearance:**
- Primary purple/blue button
- Cart plus icon on the left
- Full width on mobile, half width on desktop (grid layout)

**Functionality:**
- Click to add 1 quantity to your shopping list
- Costs 1 credit per unique item (first add)
- Additional quantities of same item = FREE
- Maximum 10 distinct items per active shopping list
- Toast notification on success: "Dodato u listu!"

**Error Handling:**
- Shows error toast if 10-item limit reached
- Shows error toast if insufficient credits (402 error)
- Disables button while adding (prevents double-clicks)

---

## 3. 📄 DETAILS BUTTON

**Location:** Bottom-right of product card
**Label:** "Detalji"

**Appearance:**
- Secondary button (white with purple border)
- Text-only, no icon

**Functionality:**
- Opens modal with full product details
- Shows business info, location, contact
- Shows product image, price, expiration date
- Optional: Google Maps link for store location

---

## API Endpoints Used

### Favorites
```
POST /api/favorites
- Body: { product_id: number }
- Cost: 1 credit (idempotent)
- Returns: { success, favorite_id }

DELETE /api/favorites/{favorite_id}
- Returns: { success }

GET /api/favorites
- Returns: { favorites: [...] }
```

### Shopping List
```
POST /api/shopping-list/items
- Body: { product_id, offer_id, qty }
- Cost: 1 credit per distinct item
- Limit: 10 distinct items per active list
- Returns: { success, item_id, shopping_list_id }
```

---

## User Flow Examples

### Adding to Favorites
1. User hovers over product tile
2. Sees heart icon in top-left corner
3. Clicks heart icon
4. Icon fills with red color
5. Toast shows: "Dodato u omiljene!"
6. Header badge updates (+1)
7. 1 credit deducted

### Adding to Shopping List
1. User clicks "Dodaj" button
2. Button shows loading state (disabled)
3. Item added to active shopping list (or new list created)
4. Toast shows: "Dodato u listu!"
5. Cart icon badge updates with item count
6. 1 credit deducted (first time for this product)

### Viewing Details
1. User clicks "Detalji" button OR product image
2. Modal opens with full product info
3. User can see:
   - Business name and logo
   - Full product description
   - Price (current and old)
   - Expiration date
   - Location and contact info
   - Google Maps link (if available)

---

## Credit System

| Action | Cost | Notes |
|--------|------|-------|
| Add to Favorites | 1 credit | First time only (idempotent) |
| Add to Shopping List | 1 credit | Per distinct product |
| Increase Quantity | FREE | Same product, more quantity |
| View Details | FREE | Always free |
| Checkout Shopping List | FREE | Currently free (promo) |

---

## Frontend Components

1. **FavoriteButton.vue**
   - Reusable heart button component
   - Integrates with useFavoritesStore
   - Shows filled/outline based on state

2. **ProductCard.vue**
   - Main product tile component
   - Includes all 3 buttons
   - Used on homepage and /proizvodi page

3. **Stores:**
   - `stores/favorites.ts` - Manages favorites state
   - `stores/cart.ts` - Manages shopping list state

4. **Composables:**
   - `composables/useCreditsToast.ts` - Handles toast notifications and 402 errors

---

## Where These Buttons Appear

✅ **Homepage** - Featured products section
✅ **/proizvodi** - All products grid
✅ **Search results** - AI search results
❌ **Modal details view** - Could be added later
❌ **/favorites page** - Already has remove button only

---

## Next Steps / Future Enhancements

1. **Notifications System**
   - Email notifications when favorited products get new discounts
   - Browser push notifications
   - SMS notifications (Twilio integration exists)

2. **Favorites Management**
   - Bulk remove from favorites
   - Categories for favorites
   - Price drop history

3. **Shopping List Improvements**
   - Multiple lists (home, work, gift)
   - Share lists with others
   - Recurring lists

4. **Analytics**
   - Track most favorited products
   - Track conversion rate (favorite → shopping list)
   - Popular products trending
