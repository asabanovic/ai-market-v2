# Promo Popup Framework - Planned Work

## Current Implementation (Simple)

We currently track promo popups seen using the existing `preferences` JSONB field on the User model:

```python
preferences = {
    "grocery_interests": [...],
    "seen_promos": {
        "submission_promo": 1,  # view count
        "mobile_app_promo": 2
    }
}
```

### Endpoints
- `POST /auth/user/promo-seen` - Mark a promo as seen (increments view count)
- `GET /auth/verify` - Returns `preferences.seen_promos` with user data

### Frontend
- `PromoSubmissionPopup.vue` - First promo popup component
- Logic in `app.vue` to show popups based on `user.preferences.seen_promos`

---

## Full Framework (Future Implementation)

For a full admin-controlled popup system, implement the following:

### Database Models

```python
class PromoPopup(db.Model):
    """Admin-managed promotional popups"""
    __tablename__ = 'promo_popups'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # 'mobile_app_launch'

    # Content
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    content = db.Column(db.Text)  # HTML or markdown
    image_url = db.Column(db.String(500))  # Optional header image

    # CTA (Call to Action)
    cta_text = db.Column(db.String(100))  # "Prijavi ponudu"
    cta_url = db.Column(db.String(500))   # "/prijavi-ponudu"
    cta_style = db.Column(db.String(50), default='primary')  # 'primary', 'secondary', 'gradient'

    # Display rules
    max_views = db.Column(db.Integer, default=1)  # Show N times per user (0 = unlimited)
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)  # Higher = show first

    # Targeting
    target_audience = db.Column(db.String(50), default='logged_in')
    # Options: 'all', 'logged_in', 'logged_out', 'new_users', 'premium_users'

    # Scheduling
    start_date = db.Column(db.DateTime)  # null = immediately
    end_date = db.Column(db.DateTime)    # null = forever

    # Trigger conditions (JSONB)
    trigger_conditions = db.Column(JSONB, default={})
    # Examples:
    # {"page": "/"}  - Show on homepage
    # {"min_searches": 5}  - Show after 5 searches
    # {"days_since_signup": 7}  - Show 7 days after signup
    # {"has_no_submissions": true}  - Show to users who haven't submitted

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String, db.ForeignKey('users.id'))


class UserPopupView(db.Model):
    """Track popup views and interactions per user"""
    __tablename__ = 'user_popup_views'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    popup_id = db.Column(db.Integer, db.ForeignKey('promo_popups.id'), nullable=False)

    view_count = db.Column(db.Integer, default=0)
    first_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime)
    dismissed_at = db.Column(db.DateTime)  # When user clicked X or "later"
    clicked_cta_at = db.Column(db.DateTime)  # When user clicked CTA

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'popup_id', name='unique_user_popup'),
    )
```

### API Endpoints

```python
# User endpoints
GET  /api/popups/pending      # Get next popup to show for current user
POST /api/popups/{id}/view    # Increment view count
POST /api/popups/{id}/dismiss # Mark as dismissed
POST /api/popups/{id}/click   # Track CTA click

# Admin endpoints
GET    /api/admin/popups           # List all popups with stats
POST   /api/admin/popups           # Create new popup
GET    /api/admin/popups/{id}      # Get popup details
PUT    /api/admin/popups/{id}      # Update popup
DELETE /api/admin/popups/{id}      # Delete popup
GET    /api/admin/popups/{id}/stats # View analytics (views, clicks, dismissals)
POST   /api/admin/popups/reorder   # Reorder popup priorities
```

### Frontend Components

```
frontend/
├── components/
│   ├── PromoPopupModal.vue      # Generic renderer for any popup
│   └── PromoPopupRenderer.vue   # Handles fetching and showing pending popup
├── composables/
│   └── usePromoPopups.ts        # Fetch pending, track views/clicks
└── pages/admin/
    └── popups.vue               # Admin management UI
```

### PromoPopupModal.vue (Generic)

```vue
<template>
  <Teleport to="body">
    <div v-if="popup" class="fixed inset-0 z-50">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/60" @click="dismiss"></div>

      <!-- Modal -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-white rounded-2xl max-w-md w-full overflow-hidden">
          <!-- Close button -->
          <button @click="dismiss" class="absolute top-4 right-4">
            <Icon name="mdi:close" />
          </button>

          <!-- Image header (if provided) -->
          <img v-if="popup.image_url" :src="popup.image_url" class="w-full h-48 object-cover" />

          <!-- Content -->
          <div class="p-6">
            <h3 class="text-2xl font-bold mb-2">{{ popup.title }}</h3>
            <p v-if="popup.subtitle" class="text-gray-600 mb-4">{{ popup.subtitle }}</p>
            <div v-if="popup.content" v-html="popup.content" class="prose mb-6"></div>

            <!-- CTA -->
            <button
              v-if="popup.cta_text"
              @click="handleCTA"
              :class="ctaClasses"
            >
              {{ popup.cta_text }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

### Admin Dashboard Features

1. **Popup List View**
   - Table with: Title, Status (active/inactive), Views, Clicks, CTR, Date Range
   - Quick toggle active/inactive
   - Drag-and-drop reorder priority

2. **Create/Edit Popup**
   - Rich text editor for content
   - Image upload
   - Preview before saving
   - Scheduling (start/end dates)
   - Target audience selector
   - Max views setting

3. **Analytics**
   - Views over time chart
   - Click-through rate (CTR)
   - Dismissal rate
   - Time to interaction
   - Conversion funnel (view → click → action)

---

## Migration Path

1. **Phase 1 (Current)**: Simple `seen_promos` in preferences JSONB
2. **Phase 2**: Add `PromoPopup` model, migrate existing promos to DB
3. **Phase 3**: Add `UserPopupView` for detailed analytics
4. **Phase 4**: Build admin UI
5. **Phase 5**: Add trigger conditions and advanced targeting

---

## Example Popups to Create

1. **submission_promo** - "Našli ste fenomenalnu ponudu?" (Current)
2. **mobile_app_promo** - Promote mobile app download
3. **referral_promo** - Encourage users to invite friends
4. **premium_upsell** - Upsell premium features
5. **feedback_request** - Ask for app store review
6. **seasonal_promo** - Holiday/sale event announcements
