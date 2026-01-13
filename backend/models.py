# Database models for the marketplace application
from datetime import datetime, date
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, JSON
from pgvector.sqlalchemy import Vector
import json
import hashlib
import secrets

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Additional fields for marketplace
    password_hash = db.Column(db.String, nullable=True)  # For email/password registration
    reset_token = db.Column(db.String, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=True, index=True)
    _city_legacy = db.Column('city', db.String, nullable=True)  # Legacy column, kept for migration
    preferences = db.Column(JSON, nullable=True)  # JSON field for user preferences
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), default=1)
    
    # Email verification fields
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    verification_email_sent_at = db.Column(db.DateTime, nullable=True)  # When verification email was last sent
    is_admin = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Last login tracking
    last_login = db.Column(db.DateTime, nullable=True)

    # Phone number for SMS notifications and authentication
    phone = db.Column(db.String, unique=True, nullable=True)
    phone_verified = db.Column(db.Boolean, default=False)

    # Track registration method: 'email' or 'phone'
    registration_method = db.Column(db.String, default='email', nullable=True)

    # WhatsApp availability - user preference for OTP delivery
    whatsapp_available = db.Column(db.Boolean, default=True, nullable=False)

    # Notification preferences: 'none', 'favorites', 'all'
    notification_preferences = db.Column(db.String, default='none', nullable=True)

    # Onboarding flag - True if user completed initial setup
    onboarding_completed = db.Column(db.Boolean, default=False)

    # Welcome guide flag - True if user has seen the welcome guide popup
    welcome_guide_seen = db.Column(db.Boolean, default=False)

    # Weekly credits system (LEGACY - kept for backward compatibility)
    weekly_credits = db.Column(db.Integer, default=40)
    weekly_credits_used = db.Column(db.Integer, default=0)
    weekly_credits_reset_date = db.Column(db.Date, default=date.today)

    # Monthly credits system - Two buckets:
    # 1. Regular credits: 40 credits per month (reset on 1st of each month)
    monthly_credits = db.Column(db.Integer, default=40)  # Regular credits (reset monthly)
    monthly_credits_used = db.Column(db.Integer, default=0)
    monthly_credits_reset_date = db.Column(db.Date, default=date.today)

    # 2. Extra credits: Earned credits (referrals, engagement) - these accumulate
    extra_credits = db.Column(db.Integer, default=0)  # Never reset, can go up or down

    # First search reward - bonus credits for completing first search
    first_search_reward_claimed = db.Column(db.Boolean, default=False, nullable=False)

    # Feedback bonus tracking - user gets +5 credits per feedback, once per 40 credits spent
    # Value represents number of feedback bonuses already claimed
    # User can claim bonus N+1 when total_credits_spent >= N * 40
    feedback_bonuses_claimed = db.Column(db.Integer, default=0, nullable=False)

    # Lifetime credits spent - tracks total credits ever spent (never resets)
    lifetime_credits_spent = db.Column(db.Integer, default=0, nullable=False)

    # Referral system
    referral_code = db.Column(db.String(20), unique=True, nullable=True)  # Auto-generated unique code
    custom_referral_code = db.Column(db.String(50), unique=True, nullable=True)  # User-chosen custom code (e.g., "adnan")
    custom_code_changed = db.Column(db.Boolean, default=False, nullable=False)  # Has user customized their auto-generated code?
    referred_by_code = db.Column(db.String(20), nullable=True)  # Who referred this user

    # Streak system - daily activity tracking
    current_streak = db.Column(db.Integer, default=0, nullable=False)  # Current consecutive days
    longest_streak = db.Column(db.Integer, default=0, nullable=False)  # All-time longest streak
    last_activity_date = db.Column(db.Date, nullable=True)  # Last day user was active
    last_streak_milestone = db.Column(db.Integer, default=0, nullable=False)  # Last milestone rewarded (3, 7, 14, 30, 60)

    # First-touch attribution tracking
    first_touch_source = db.Column(db.String(100), nullable=True)  # e.g., 'facebook', 'google', 'email', 'direct'
    first_touch_medium = db.Column(db.String(100), nullable=True)  # e.g., 'cpc', 'social', 'email'
    first_touch_campaign = db.Column(db.String(255), nullable=True)  # e.g., 'winter_sale_2025'
    first_touch_fbclid = db.Column(db.String(255), nullable=True)  # Facebook click ID if present
    first_touch_timestamp = db.Column(db.DateTime, nullable=True)  # When user first landed
    first_touch_landing_page = db.Column(db.String(500), nullable=True)  # URL path where user first landed
    first_touch_referrer = db.Column(db.String(500), nullable=True)  # Original referrer URL

    # PWA tracking - track users who access via installed PWA
    is_pwa_user = db.Column(db.Boolean, default=False, nullable=False)  # True if ever accessed via PWA
    last_pwa_access = db.Column(db.DateTime, nullable=True)  # Last time accessed from PWA
    pwa_access_count = db.Column(db.Integer, default=0, nullable=False)  # Number of PWA sessions

    # Relationships
    package = db.relationship('Package', backref='users')
    city_rel = db.relationship('City', backref='users', lazy='joined')
    searches = db.relationship('UserSearch', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    shopping_lists = db.relationship('ShoppingList', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    credit_transactions = db.relationship('CreditTransaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def city(self):
        """Get city name from relationship or legacy column"""
        if self.city_rel:
            return self.city_rel.name
        return self._city_legacy

    @city.setter
    def city(self, value):
        """Set city - accepts city name (string) or city_id (int)"""
        if value is None:
            self.city_id = None
            self._city_legacy = None
        elif isinstance(value, int):
            self.city_id = value
        elif isinstance(value, str):
            # Look up city by name
            from models import City
            city_obj = City.query.filter_by(name=value).first()
            if city_obj:
                self.city_id = city_obj.id
            else:
                # Store in legacy column if city not found in DB
                self._city_legacy = value

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id, ondelete='CASCADE'))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Packages table for query limits
class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    daily_limit = db.Column(db.Integer, nullable=False)

# Cities table with coordinates
class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    country = db.Column(db.String, default='Bosnia and Herzegovina')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<City {self.name} ({self.latitude}, {self.longitude})>'

# Businesses table
class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=True, index=True)  # URL-friendly identifier
    contact_phone = db.Column(db.String, nullable=True)
    city = db.Column(db.String, default='Tuzla')
    pdf_url = db.Column(db.String, nullable=True)
    google_link = db.Column(db.String, nullable=True)
    logo_path = db.Column(db.String, nullable=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    strike_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String, default='active')
    is_promo_active = db.Column(db.Boolean, default=True)  # Show on homepage if True
    views = db.Column(db.Integer, default=0)

    # Exclusive coupons fields
    business_type = db.Column(db.String(50), default='supermarket')  # 'supermarket' or 'local_business'
    description = db.Column(db.Text, nullable=True)  # Business description
    address = db.Column(db.String(300), nullable=True)  # Full address
    working_hours = db.Column(JSON, nullable=True)  # {"mon": "08:00-20:00", "tue": "08:00-20:00", ...}
    has_exclusive_coupons = db.Column(db.Boolean, default=False)  # Enabled for exclusive coupons
    max_campaigns_allowed = db.Column(db.Integer, default=1)  # Max campaigns for this business (admin can increase)
    average_rating = db.Column(db.Float, default=0.0)  # Cached average rating
    total_reviews = db.Column(db.Integer, default=0)  # Cached total reviews count
    cover_image_path = db.Column(db.String, nullable=True)  # Large storefront/cover image for landing page

    # Relationships
    products = db.relationship('Product', backref='business', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generate_slug(name, city=None):
        """Generate URL-friendly slug from business name"""
        import re
        import unicodedata
        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', name.lower())
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        # Add city suffix if provided for uniqueness
        if city:
            city_slug = unicodedata.normalize('NFKD', city.lower())
            city_slug = city_slug.encode('ascii', 'ignore').decode('ascii')
            city_slug = re.sub(r'[^a-z0-9]+', '-', city_slug).strip('-')
            slug = f"{slug}-{city_slug}"
        return slug

    @staticmethod
    def generate_google_maps_link(business_name: str, latitude: float, longitude: float, zoom: int = 12) -> str:
        """
        Generate a Google Maps search link for a business at given coordinates.

        Example output:
        https://www.google.com/maps/search/bingo+supermarket/@43.8379881,18.350948,12z
        """
        import urllib.parse
        # Format business name for URL (replace spaces with +)
        search_query = urllib.parse.quote_plus(business_name)
        return f"https://www.google.com/maps/search/{search_query}/@{latitude},{longitude},{zoom}z"

    def get_google_link_for_city(self, city_name: str = None) -> str:
        """
        Get Google Maps link for this business in a specific city.
        If city_name is None, uses the business's default city.
        Returns the stored google_link if no city coordinates found.
        """
        target_city = city_name or self.city
        if not target_city:
            return self.google_link

        # Get city coordinates
        city = City.query.filter_by(name=target_city).first()
        if city and city.latitude and city.longitude:
            return Business.generate_google_maps_link(self.name, city.latitude, city.longitude)

        # Fallback to stored google_link
        return self.google_link

    def is_open_now(self, timezone_offset=1):
        """
        Check if business is currently open based on working_hours.
        timezone_offset: Bosnia is UTC+1 (CET) or UTC+2 (CEST)
        Returns: True if open, False if closed, None if no working hours set
        """
        if not self.working_hours:
            return None

        from datetime import datetime, timedelta
        import pytz

        # Get current time in Bosnia timezone
        bosnia_tz = pytz.timezone('Europe/Sarajevo')
        now = datetime.now(bosnia_tz)

        # Get day name (lowercase)
        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        current_day = day_names[now.weekday()]

        hours = self.working_hours.get(current_day)
        if not hours or hours.lower() in ['closed', 'zatvoreno', '']:
            return False

        try:
            # Parse hours like "08:00-20:00"
            open_time, close_time = hours.split('-')
            open_hour, open_min = map(int, open_time.strip().split(':'))
            close_hour, close_min = map(int, close_time.strip().split(':'))

            current_minutes = now.hour * 60 + now.minute
            open_minutes = open_hour * 60 + open_min
            close_minutes = close_hour * 60 + close_min

            return open_minutes <= current_minutes <= close_minutes
        except (ValueError, AttributeError):
            return None

    def get_active_coupons_count(self):
        """Get count of currently active coupons for this business"""
        return Coupon.query.filter_by(
            business_id=self.id,
            is_active=True
        ).filter(Coupon.remaining_quantity > 0).count()

    def get_campaigns_count(self):
        """Get count of campaigns for this business"""
        return Campaign.query.filter_by(business_id=self.id).count()

    def get_active_campaigns_count(self):
        """Get count of active campaigns for this business"""
        return Campaign.query.filter_by(business_id=self.id, is_active=True).count()

    def can_create_campaign(self):
        """Check if business can create more campaigns"""
        return self.get_campaigns_count() < self.max_campaigns_allowed

    def update_rating_cache(self):
        """Update cached average rating and total reviews"""
        from sqlalchemy import func
        result = db.session.query(
            func.avg(UserCoupon.buyer_to_business_rating),
            func.count(UserCoupon.id)
        ).join(Coupon).filter(
            Coupon.business_id == self.id,
            UserCoupon.buyer_to_business_rating.isnot(None)
        ).first()

        self.average_rating = round(result[0] or 0, 1)
        self.total_reviews = result[1] or 0


class Store(db.Model):
    """
    Physical store location for a business.
    A business can have multiple stores (locations) in different areas.
    Each store can have its own address, working hours, and be associated with coupons.
    """
    __tablename__ = 'stores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)

    # Store info
    name = db.Column(db.String(200), nullable=False)  # e.g., "Mesnica Tuzla - Centar"
    address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=True)

    # Location
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    google_maps_link = db.Column(db.String, nullable=True)

    # Working hours (per day, like business)
    working_hours = db.Column(JSON, nullable=True)  # {"mon": "08:00-20:00", ...}

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)  # Primary/main store location

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    business = db.relationship('Business', backref=db.backref('stores', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_stores_business', 'business_id'),
        db.Index('idx_stores_city', 'city'),
        db.Index('idx_stores_active', 'is_active'),
    )

    def is_open_now(self):
        """Check if store is currently open based on working_hours."""
        if not self.working_hours:
            return None

        import pytz
        bosnia_tz = pytz.timezone('Europe/Sarajevo')
        now = datetime.now(bosnia_tz)

        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        current_day = day_names[now.weekday()]

        hours = self.working_hours.get(current_day)
        if not hours or hours.lower() in ['closed', 'zatvoreno', '']:
            return False

        try:
            open_time, close_time = hours.split('-')
            open_hour, open_min = map(int, open_time.strip().split(':'))
            close_hour, close_min = map(int, close_time.strip().split(':'))

            current_minutes = now.hour * 60 + now.minute
            open_minutes = open_hour * 60 + open_min
            close_minutes = close_hour * 60 + close_min

            return open_minutes <= current_minutes <= close_minutes
        except (ValueError, AttributeError):
            return None

    def to_dict(self):
        """Convert store to dictionary for API responses"""
        return {
            'id': self.id,
            'business_id': self.business_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'phone': self.phone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'google_maps_link': self.google_maps_link,
            'working_hours': self.working_hours,
            'is_active': self.is_active,
            'is_primary': self.is_primary,
            'is_open': self.is_open_now()
        }


# Products table
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    city = db.Column(db.String, nullable=True)
    title = db.Column(db.String, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    expires = db.Column(db.Date, nullable=True)
    category = db.Column(db.String, nullable=True)
    category_group = db.Column(db.String, nullable=True)  # Simplified category: meso, mlijeko, pica, etc.
    tags = db.Column(JSON, nullable=True)  # JSON array
    product_metadata = db.Column(JSON, nullable=True)  # JSON object (renamed from metadata)
    image_path = db.Column(db.String, nullable=True)
    original_image_path = db.Column(db.String, nullable=True)  # First uploaded image (immutable)
    suggested_images = db.Column(JSON, nullable=True)  # Array of S3 paths for AI-suggested images
    product_url = db.Column(db.String, nullable=True)
    views = db.Column(db.Integer, default=0)
    content_hash = db.Column(db.String, nullable=True)  # Hash to detect content changes for embeddings
    enriched_description = db.Column(db.Text, nullable=True)  # AI-generated rich description
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Product matching fields for clone/sibling detection
    brand = db.Column(db.String, nullable=True, index=True)  # e.g., "Ariel", "Meggle", "Milka"
    product_type = db.Column(db.String, nullable=True, index=True)  # Normalized type: "mlijeko", "deterdžent", "čokolada"
    size_value = db.Column(db.Float, nullable=True)  # Numeric size: 1, 0.5, 500, 200
    size_unit = db.Column(db.String, nullable=True)  # Unit: "kg", "l", "ml", "g", "kom"
    variant = db.Column(db.String, nullable=True)  # Meta field for differentiators: "light", "bez laktoze", "gorka"
    match_key = db.Column(db.String, nullable=True, index=True)  # Auto-generated: "brand:type:size" for clone detection

    @property
    def has_discount(self):
        """Check if product has an active (non-expired) discount"""
        if self.discount_price is None or self.discount_price >= self.base_price:
            return False
        # Check if discount has expired
        if self.expires and date.today() > self.expires:
            return False
        return True
    
    @property
    def discount_percentage(self):
        if self.has_discount:
            return round(((self.base_price - self.discount_price) / self.base_price) * 100)
        return 0
    
    @property
    def is_expired(self):
        if self.expires:
            return date.today() > self.expires
        return False

    def generate_match_key(self):
        """Generate a match key from brand, product_type, variant, size_value, size_unit for clone detection.
        Brand is optional - if unknown/null, it will be omitted from the key."""
        # Require at minimum: product_type, size_value, size_unit
        if not self.product_type or self.size_value is None or not self.size_unit:
            return None
        # Normalize: lowercase, strip whitespace
        # Brand can be null/unknown - exclude from key if so
        brand = self.brand.lower().strip() if self.brand and self.brand.lower() not in ['unknown', ''] else None
        product_type = self.product_type.lower().strip()
        variant = self.variant.lower().strip() if self.variant else ''
        # Format size: normalize units (e.g., 1000ml -> 1l, 1000g -> 1kg)
        size_value = self.size_value
        size_unit = self.size_unit.lower().strip()
        # Normalize large units
        if size_unit == 'ml' and size_value >= 1000:
            size_value = size_value / 1000
            size_unit = 'l'
        elif size_unit == 'g' and size_value >= 1000:
            size_value = size_value / 1000
            size_unit = 'kg'
        # Format: remove trailing zeros from float
        size_str = f"{size_value:g}" if size_value == int(size_value) else f"{size_value:.2f}".rstrip('0').rstrip('.')
        # Build match key - brand is optional
        parts = []
        if brand:
            parts.append(brand)
        parts.append(product_type)
        if variant:
            parts.append(variant)
        parts.append(f"{size_str}{size_unit}")
        return ':'.join(parts)

    def update_match_key(self):
        """Update the match_key field based on current values"""
        self.match_key = self.generate_match_key()


# Product embeddings table for semantic search
class ProductEmbedding(db.Model):
    __tablename__ = 'product_embeddings'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    embedding = db.Column(Vector(1536), nullable=False)  # OpenAI text-embedding-3-small dimension
    embedding_text = db.Column(db.Text, nullable=True)  # Text that was embedded
    model_version = db.Column(db.String, nullable=True)  # e.g., 'text-embedding-3-small'
    content_hash = db.Column(db.String, nullable=True)  # Hash to detect when product content changes
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    product = db.relationship('Product', backref=db.backref('embedding_data', passive_deletes=True), lazy=True)

# Product price history table for tracking price changes
class ProductPriceHistory(db.Model):
    __tablename__ = 'product_price_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationship
    product = db.relationship('Product', backref=db.backref('price_history', passive_deletes=True), lazy=True)

    __table_args__ = (
        db.Index('idx_price_history_product_id', 'product_id'),
        db.Index('idx_price_history_recorded_at', 'recorded_at'),
    )


# Product matches table for tracking relationships between products across stores
class ProductMatch(db.Model):
    __tablename__ = 'product_matches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # The two products being matched
    product_a_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    product_b_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)

    # Match type:
    # - 'clone': Same brand + type + size in different stores (exact product)
    # - 'brand_variant': Same type + size, different brand (competitor products)
    # - 'sibling': Same type, different size/brand (related products)
    match_type = db.Column(db.String, nullable=False)

    # Confidence score (0-100) for automated matches
    confidence = db.Column(db.Integer, nullable=True)

    # How the match was created: 'auto' (cron job) or 'manual' (admin)
    created_by = db.Column(db.String, default='auto')

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    product_a = db.relationship('Product', foreign_keys=[product_a_id], backref=db.backref('matches_as_a', passive_deletes=True))
    product_b = db.relationship('Product', foreign_keys=[product_b_id], backref=db.backref('matches_as_b', passive_deletes=True))

    __table_args__ = (
        # Ensure we don't have duplicate matches (A-B is same as B-A)
        db.UniqueConstraint('product_a_id', 'product_b_id', 'match_type', name='uq_product_match'),
        db.Index('idx_product_matches_product_a', 'product_a_id'),
        db.Index('idx_product_matches_product_b', 'product_b_id'),
        db.Index('idx_product_matches_type', 'match_type'),
    )

    @staticmethod
    def get_or_create_match(product_a_id, product_b_id, match_type, confidence=None, created_by='auto'):
        """Create a match if it doesn't exist, ensuring consistent ordering"""
        # Always store with smaller ID first to prevent duplicates
        if product_a_id > product_b_id:
            product_a_id, product_b_id = product_b_id, product_a_id

        existing = ProductMatch.query.filter_by(
            product_a_id=product_a_id,
            product_b_id=product_b_id,
            match_type=match_type
        ).first()

        if existing:
            return existing, False

        match = ProductMatch(
            product_a_id=product_a_id,
            product_b_id=product_b_id,
            match_type=match_type,
            confidence=confidence,
            created_by=created_by
        )
        db.session.add(match)
        return match, True


# User searches table for tracking
class UserSearch(db.Model):
    __tablename__ = 'user_searches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # Allow null for anonymous searches
    user_ip = db.Column(db.String(50), nullable=True)  # For tracking anonymous users
    query = db.Column(db.String, nullable=False)
    results = db.Column(JSON, nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)  # Browser user agent string
    device_type = db.Column(db.String(50), nullable=True)  # mobile, tablet, desktop
    browser = db.Column(db.String(100), nullable=True)  # Chrome, Firefox, Safari, etc.
    os = db.Column(db.String(100), nullable=True)  # Windows, macOS, iOS, Android, etc.
    only_discounted = db.Column(db.Boolean, default=False)  # Whether "Samo popusti" filter was used
    created_at = db.Column(db.DateTime, default=datetime.now)

# Contact messages table
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String, nullable=True)
    user_email = db.Column(db.String, nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# OTP codes for phone authentication
class OTPCode(db.Model):
    __tablename__ = 'otp_codes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String, nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.Index('idx_otp_phone_expires', 'phone', 'expires_at'),
    )

# Referral tracking table
class Referral(db.Model):
    __tablename__ = 'referrals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    referrer_code = db.Column(db.String(20), db.ForeignKey('users.referral_code', ondelete='CASCADE'), nullable=False)  # Who referred
    referred_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # Who was referred
    credits_awarded = db.Column(db.Integer, default=100)  # Credits given to referrer
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    referred_user = db.relationship('User', foreign_keys=[referred_user_id], backref='referral_source')

    __table_args__ = (
        db.Index('idx_referrals_referrer_code', 'referrer_code'),
        db.Index('idx_referrals_referred_user', 'referred_user_id'),
    )

# Business membership for user-business relationships
class BusinessMembership(db.Model):
    __tablename__ = 'business_memberships'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String, nullable=False, default='staff')  # owner > manager > staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    business = db.relationship('Business', backref='memberships')
    user = db.relationship('User', backref='business_memberships')
    
    __table_args__ = (UniqueConstraint('business_id', 'user_id', name='uq_business_user'),)

# Business invitations for email-based invites
class BusinessInvitation(db.Model):
    __tablename__ = 'business_invitations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    email = db.Column(db.String, nullable=False)
    token_hash = db.Column(db.String, unique=True, nullable=False)
    role = db.Column(db.String, nullable=False, default='staff')
    invited_by_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    redeemed_by_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    business = db.relationship('Business', backref='invitations')
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id], backref='sent_invitations')
    redeemed_by = db.relationship('User', foreign_keys=[redeemed_by_user_id], backref='accepted_invitations')
    
    @staticmethod
    def generate_token():
        """Generate a secure invitation token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token):
        """Hash a token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return datetime.now() > self.expires_at
    
    @property
    def is_accepted(self):
        """Check if invitation has been accepted"""
        return self.accepted_at is not None
    
    @property
    def is_revoked(self):
        """Check if invitation has been revoked"""
        return self.revoked_at is not None
    
    @property
    def is_active(self):
        """Check if invitation is still active and can be used"""
        return not self.is_expired and not self.is_accepted and not self.is_revoked

# Savings statistics table for marketing tracking
class SavingsStatistics(db.Model):
    __tablename__ = 'savings_statistics'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_products_served = db.Column(db.Integer, default=0, nullable=False)
    total_savings_amount = db.Column(db.Float, default=0.0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @classmethod
    def get_or_create_stats(cls):
        """Get the single statistics record, create if doesn't exist"""
        stats = cls.query.first()
        if not stats:
            stats = cls()
            db.session.add(stats)
            db.session.commit()
        return stats
    
    @classmethod
    def add_savings(cls, products_count, savings_amount):
        """Add to the total savings and products served"""
        stats = cls.get_or_create_stats()
        stats.total_products_served += products_count
        stats.total_savings_amount += savings_amount
        db.session.commit()
        return stats

# Role hierarchy helper functions
def get_role_precedence(role):
    """Get numeric precedence for role comparison (higher = more permissions)"""
    roles = {'staff': 1, 'manager': 2, 'owner': 3}
    return roles.get(role, 0)

def user_has_business_role(user_id, business_id, min_role='staff'):
    """Check if user has required role for business"""
    if not user_id or not business_id:
        return False

    # Check if user is admin
    user = User.query.get(user_id)
    if user and user.is_admin:
        return True

    # Check business membership
    membership = BusinessMembership.query.filter_by(
        user_id=user_id,
        business_id=business_id,
        is_active=True
    ).first()

    if not membership:
        return False

    # Compare role precedence
    return get_role_precedence(membership.role) >= get_role_precedence(min_role)

# ==================== SHOPPING LIST & FAVORITES MODELS ====================

# Credit transactions for tracking credit usage
class CreditTransaction(db.Model):
    __tablename__ = 'credit_transactions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    delta = db.Column(db.Integer, nullable=False)  # Positive for additions, negative for deductions
    balance_after = db.Column(db.Integer, nullable=False)  # Snapshot of balance after transaction
    action = db.Column(db.String, nullable=False)  # e.g., 'ADD_TO_CART', 'ADD_FAVORITE', 'CHECKOUT_SMS', 'TOP_UP'
    transaction_metadata = db.Column(JSON, nullable=True)  # Additional context (product_id, promo=True, etc.)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_credit_transactions_user_id', 'user_id'),
    )

# User favorites/bookmarks for products
class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    product = db.relationship('Product', backref=db.backref('favorites', passive_deletes=True))

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_favorite'),
        db.Index('idx_favorites_user_id', 'user_id'),
        db.Index('idx_favorites_product_id', 'product_id'),
    )

# Shopping lists with 24-hour expiry
class ShoppingList(db.Model):
    __tablename__ = 'shopping_lists'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String, nullable=False, default='ACTIVE')  # ACTIVE, EXPIRED, SENT, CANCELLED, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=False)  # created_at + 24 hours
    sent_at = db.Column(db.DateTime, nullable=True)  # When SMS was sent
    completed_at = db.Column(db.DateTime, nullable=True)  # When all items were purchased

    # Relationships
    items = db.relationship('ShoppingListItem', backref='shopping_list', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_shopping_lists_user_status', 'user_id', 'status'),
        db.Index('idx_shopping_lists_expires_at', 'expires_at'),
        db.Index('idx_shopping_lists_completed', 'completed_at'),
    )

    @property
    def ttl_seconds(self):
        """Calculate time-to-live in seconds"""
        if self.status != 'ACTIVE':
            return 0
        delta = self.expires_at - datetime.now()
        return max(0, int(delta.total_seconds()))

    @property
    def is_active(self):
        """Check if list is active and not expired"""
        return self.status == 'ACTIVE' and datetime.now() < self.expires_at

    @property
    def purchased_count(self):
        """Count how many items have been purchased"""
        return self.items.filter(ShoppingListItem.purchased_at.isnot(None)).count()

    @property
    def total_items(self):
        """Total number of items in list"""
        return self.items.count()

# Shopping list items with price snapshots
class ShoppingListItem(db.Model):
    __tablename__ = 'shopping_list_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)  # Store-specific offer
    qty = db.Column(db.Integer, default=1, nullable=False)

    # Price snapshots at time of addition
    price_snapshot = db.Column(db.Float, nullable=False)
    old_price_snapshot = db.Column(db.Float, nullable=True)
    discount_percent_snapshot = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    purchased_at = db.Column(db.DateTime, nullable=True)  # When item was marked as purchased

    # Relationships
    product = db.relationship('Product', backref=db.backref('shopping_list_items', passive_deletes=True))
    business = db.relationship('Business', backref='shopping_list_items')

    __table_args__ = (
        UniqueConstraint('list_id', 'product_id', 'business_id', name='uq_list_product_business'),
        db.Index('idx_shopping_list_items_list_id', 'list_id'),
        db.Index('idx_shopping_list_items_purchased', 'purchased_at'),
    )

    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return round(self.price_snapshot * self.qty, 2)

    @property
    def estimated_saving(self):
        """Calculate estimated savings if there was an old price"""
        if self.old_price_snapshot and self.old_price_snapshot > self.price_snapshot:
            return round((self.old_price_snapshot - self.price_snapshot) * self.qty, 2)
        return 0

    @property
    def is_purchased(self):
        """Check if item has been purchased"""
        return self.purchased_at is not None

# SMS outbox for queued messages
class SMSOutbox(db.Model):
    __tablename__ = 'sms_outbox'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id', ondelete='SET NULL'), nullable=True)
    phone = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String, nullable=False, default='QUEUED')  # QUEUED, SENT, FAILED
    provider_message_id = db.Column(db.String, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    sent_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='sms_messages')
    list = db.relationship('ShoppingList', backref='sms_messages')

    __table_args__ = (
        db.Index('idx_sms_outbox_status', 'status'),
        db.Index('idx_sms_outbox_created_at', 'created_at'),
    )

# ==================== PRODUCT ENGAGEMENT MODELS ====================

# Product comments - users can comment on products
class ProductComment(db.Model):
    __tablename__ = 'product_comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)  # 20-1000 characters
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    product = db.relationship('Product', backref=db.backref('comments', passive_deletes=True))
    user = db.relationship('User', backref='product_comments')

    __table_args__ = (
        db.Index('idx_product_comments_product_id', 'product_id'),
        db.Index('idx_product_comments_user_id', 'user_id'),
        db.Index('idx_product_comments_created_at', 'created_at'),
    )

# Product votes - users can upvote or downvote products
class ProductVote(db.Model):
    __tablename__ = 'product_votes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    vote_type = db.Column(db.String, nullable=False)  # 'up' or 'down'
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    product = db.relationship('Product', backref=db.backref('votes', passive_deletes=True))
    user = db.relationship('User', backref='product_votes')

    __table_args__ = (
        UniqueConstraint('product_id', 'user_id', name='uq_product_user_vote'),
        db.Index('idx_product_votes_product_id', 'product_id'),
        db.Index('idx_product_votes_user_id', 'user_id'),
    )

# User engagement history - track all user engagement activities
class UserEngagement(db.Model):
    __tablename__ = 'user_engagements'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    activity_type = db.Column(db.String, nullable=False)  # 'vote_up', 'vote_down', 'comment'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    credits_earned = db.Column(db.Integer, nullable=False)  # +1 for votes, +2 for comments
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref='engagements')
    product = db.relationship('Product', backref=db.backref('engagements', passive_deletes=True))

    __table_args__ = (
        db.Index('idx_user_engagements_user_id', 'user_id'),
        db.Index('idx_user_engagements_created_at', 'created_at'),
    )

# ==================== ANONYMOUS USER TRACKING ====================

# Anonymous searches - track IP addresses for free trial searches
class AnonymousSearch(db.Model):
    __tablename__ = 'anonymous_searches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_anonymous_searches_ip', 'ip_address'),
        db.Index('idx_anonymous_searches_created_at', 'created_at'),
    )

# ==================== NOTIFICATIONS ====================

# User notifications for discount alerts and other events
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_type = db.Column(db.String, nullable=False)  # 'discount_alert', 'price_drop', etc.
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    action_url = db.Column(db.String, nullable=True)  # Optional URL to navigate to
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref='notifications')
    product = db.relationship('Product', backref=db.backref('notifications', passive_deletes=True))

    __table_args__ = (
        db.Index('idx_notifications_user_id', 'user_id'),
        db.Index('idx_notifications_created_at', 'created_at'),
        db.Index('idx_notifications_user_read', 'user_id', 'is_read'),
    )


# ==================== PRODUCT REPORTS ====================

# Product reports - users can report issues with products
class ProductReport(db.Model):
    __tablename__ = 'product_reports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.String, nullable=True)  # Optional explanation from user
    status = db.Column(db.String, nullable=False, default='pending')  # pending, reviewed, resolved, dismissed
    admin_notes = db.Column(db.Text, nullable=True)  # Admin can add notes when reviewing
    created_at = db.Column(db.DateTime, default=datetime.now)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    product = db.relationship('Product', backref=db.backref('reports', passive_deletes=True))
    user = db.relationship('User', foreign_keys=[user_id], backref='product_reports')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_reports')

    __table_args__ = (
        db.Index('idx_product_reports_product_id', 'product_id'),
        db.Index('idx_product_reports_user_id', 'user_id'),
        db.Index('idx_product_reports_status', 'status'),
        db.Index('idx_product_reports_created_at', 'created_at'),
    )


# ==================== SEARCH QUALITY TRACKING ====================

# SearchLog - detailed search result logging for quality evaluation
class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query = db.Column(db.String, nullable=False, index=True)

    # User who performed the search (null for anonymous searches)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Search type: 'text' (default) or 'camera'
    search_type = db.Column(db.String(20), nullable=True, default='text')

    # Image path for camera searches (S3 path)
    image_path = db.Column(db.String(500), nullable=True)

    # Vision analysis result for camera searches
    vision_result = db.Column(JSON, nullable=True)

    # Selected stores (business_ids) when searching
    selected_stores = db.Column(JSON, nullable=True)  # Array of business_ids

    # Search parameters used
    similarity_threshold = db.Column(db.Float, nullable=True)
    k = db.Column(db.Integer, nullable=True)

    # Results summary
    result_count = db.Column(db.Integer, nullable=False)
    total_before_filter = db.Column(db.Integer, nullable=True)

    # Detailed results with scores (JSON array)
    # Each item: {product_id, title, similarity, vector_score, text_score, rank, price, store_name}
    results_detail = db.Column(JSON, nullable=True)

    # Parsed query info from LLM (if any)
    parsed_query = db.Column(JSON, nullable=True)  # The search_items from parser

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship to user
    user = db.relationship('User', backref=db.backref('search_logs', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_search_logs_query', 'query'),
        db.Index('idx_search_logs_created_at', 'created_at'),
        db.Index('idx_search_logs_user_id', 'user_id'),
        db.Index('idx_search_logs_search_type', 'search_type'),
    )


# ==================== USER ACTIVITY TRACKING ====================

# UserActivity - detailed event logging for user interactions
class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Activity type: 'page_view', 'filter', 'pagination', 'login', etc.
    activity_type = db.Column(db.String(50), nullable=False)

    # Page or feature being used
    page = db.Column(db.String(100), nullable=True)  # e.g., 'proizvodi', 'favorites', 'home'

    # Additional context (JSON for flexible storage)
    # For page_view: {filters: {category, store, sort}, page_number}
    # For filter: {filter_type, old_value, new_value}
    # For login: {method: 'email'/'phone', ip_address}
    activity_data = db.Column(JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_activities_user_id', 'user_id'),
        db.Index('idx_user_activities_type', 'activity_type'),
        db.Index('idx_user_activities_created_at', 'created_at'),
        db.Index('idx_user_activities_user_type', 'user_id', 'activity_type'),
    )


# UserDailyVisit - track unique daily visits per user (one record per user per day)
class UserDailyVisit(db.Model):
    __tablename__ = 'user_daily_visits'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)  # The date of the visit

    # Track first and last activity time on that day
    first_seen = db.Column(db.DateTime, default=datetime.now)
    last_seen = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Count of page views on that day (optional, for extra insight)
    page_views = db.Column(db.Integer, default=1)

    # Daily bonus tracking - +2 credits for first activity of the day
    daily_bonus_claimed = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('daily_visits', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'visit_date', name='uq_user_daily_visit'),
        db.Index('idx_user_daily_visits_user_id', 'user_id'),
        db.Index('idx_user_daily_visits_date', 'visit_date'),
        db.Index('idx_user_daily_visits_user_date', 'user_id', 'visit_date'),
    )


# ProductView - track product impressions (when shown in search results/listings)
class ProductView(db.Model):
    __tablename__ = 'product_views'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    product = db.relationship('Product', backref=db.backref('views_log', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('product_views', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_product_views_product_id', 'product_id'),
        db.Index('idx_product_views_user_id', 'user_id'),
        db.Index('idx_product_views_created_at', 'created_at'),
        db.Index('idx_product_views_product_user', 'product_id', 'user_id'),
    )


# UserLogin - dedicated table for login history
class UserLogin(db.Model):
    __tablename__ = 'user_logins'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Login method: 'email', 'phone', 'google', etc.
    login_method = db.Column(db.String(20), nullable=True)

    # IP address for security/analytics
    ip_address = db.Column(db.String(50), nullable=True)

    # User agent for device tracking
    user_agent = db.Column(db.String(500), nullable=True)

    # Parsed device info from user agent
    device_type = db.Column(db.String(20), nullable=True)  # 'mobile', 'tablet', 'desktop'
    os_name = db.Column(db.String(50), nullable=True)  # 'Windows', 'macOS', 'iOS', 'Android', 'Linux'
    browser_name = db.Column(db.String(50), nullable=True)  # 'Chrome', 'Firefox', 'Safari', etc.

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('logins', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_logins_user_id', 'user_id'),
        db.Index('idx_user_logins_created_at', 'created_at'),
    )


# UserFeedback - collect user feedback and suggestions
class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # User info (nullable for anonymous users)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # For anonymous users, track by IP/session
    anonymous_id = db.Column(db.String(100), nullable=True)  # Could be IP hash or session ID

    # Rating (1-5 stars)
    rating = db.Column(db.Integer, nullable=True)

    # Feedback questions
    what_to_improve = db.Column(db.Text, nullable=True)  # "What's one thing you would improve?"
    how_to_help = db.Column(db.Text, nullable=True)  # "How can we be more helpful?"
    what_would_make_you_use = db.Column(db.Text, nullable=True)  # "What would make you use this every time you shop?"

    # General comments
    comments = db.Column(db.Text, nullable=True)

    # Context
    trigger_type = db.Column(db.String(50), nullable=True)  # 'scroll_bottom', 'credits_spent', 'manual'
    page_url = db.Column(db.String(500), nullable=True)

    # Device info
    user_agent = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('feedback', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_feedback_user_id', 'user_id'),
        db.Index('idx_user_feedback_created_at', 'created_at'),
        db.Index('idx_user_feedback_trigger', 'trigger_type'),
    )


# ==================== USER PRODUCT TRACKING ====================

class UserTrackedProduct(db.Model):
    """Extracted search terms from user preferences for daily scanning"""
    __tablename__ = 'user_tracked_products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    search_term = db.Column(db.String, nullable=False)  # Normalized search term (e.g., "mlijeko")
    original_text = db.Column(db.String, nullable=True)  # Original text from preferences
    source = db.Column(db.String, default='grocery_interests')  # Where it came from
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('tracked_products', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'search_term', name='uq_user_tracked_product'),
        db.Index('idx_tracked_products_user', 'user_id'),
        db.Index('idx_tracked_products_active', 'is_active'),
    )

    @staticmethod
    def get_preferences_hash(user):
        """Generate a hash of user preferences for change detection"""
        import hashlib
        prefs = user.preferences or {}
        grocery_interests = sorted(prefs.get('grocery_interests', []))
        typical_products = sorted(prefs.get('typical_products', []))
        combined = '|'.join(grocery_interests + typical_products)
        return hashlib.md5(combined.encode()).hexdigest()


class UserProductScan(db.Model):
    """Daily scan results metadata - one entry per user per day"""
    __tablename__ = 'user_product_scans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    scan_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String, default='completed')  # pending, running, completed, failed
    total_products_found = db.Column(db.Integer, default=0)
    new_products_count = db.Column(db.Integer, default=0)  # Products not in previous day
    new_discounts_count = db.Column(db.Integer, default=0)  # Same products but now discounted
    summary_text = db.Column(db.Text, nullable=True)  # AI-generated summary of changes
    preferences_hash = db.Column(db.String(32), nullable=True)  # Hash of preferences used for change detection
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('product_scans', lazy='dynamic'))
    results = db.relationship('UserScanResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'scan_date', name='uq_user_scan_date'),
        db.Index('idx_scans_user_date', 'user_id', 'scan_date'),
        db.Index('idx_scans_date', 'scan_date'),
    )


class UserScanResult(db.Model):
    """Individual product results per scan per tracked term"""
    __tablename__ = 'user_scan_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('user_product_scans.id', ondelete='CASCADE'), nullable=False)
    tracked_product_id = db.Column(db.Integer, db.ForeignKey('user_tracked_products.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    product_title = db.Column(db.String, nullable=True)  # Snapshot of title at scan time
    business_name = db.Column(db.String, nullable=True)  # Snapshot of business name
    similarity_score = db.Column(db.Float, nullable=True)
    base_price = db.Column(db.Float, nullable=True)  # Full price history
    discount_price = db.Column(db.Float, nullable=True)  # Full price history
    was_discounted_yesterday = db.Column(db.Boolean, default=False)
    is_new_today = db.Column(db.Boolean, default=False)  # Wasn't in yesterday's results
    price_dropped_today = db.Column(db.Boolean, default=False)  # Price lower than yesterday
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    tracked_product = db.relationship('UserTrackedProduct', backref=db.backref('scan_results', lazy='dynamic'))
    product = db.relationship('Product', backref=db.backref('tracking_results', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_scan_results_scan', 'scan_id'),
        db.Index('idx_scan_results_tracked', 'tracked_product_id'),
        db.Index('idx_scan_results_product', 'product_id'),
    )


# ==================== FEATURE FLAGS ====================

class FeatureFlag(db.Model):
    """Feature flags for controlling feature visibility"""
    __tablename__ = 'feature_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def is_enabled(cls, key, default=False):
        """Check if a feature flag is enabled"""
        flag = cls.query.filter_by(key=key).first()
        return flag.value if flag else default

    @classmethod
    def set_flag(cls, key, value, description=None):
        """Set or create a feature flag"""
        flag = cls.query.filter_by(key=key).first()
        if flag:
            flag.value = value
            if description:
                flag.description = description
        else:
            flag = cls(key=key, value=value, description=description)
            db.session.add(flag)
        db.session.commit()
        return flag


# ==================== EXCLUSIVE COUPONS ====================

class Campaign(db.Model):
    """Campaign groups coupons together. Each business can have limited campaigns."""
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)

    # Campaign info
    name = db.Column(db.String(200), nullable=False)  # "Božićna Akcija 2025"
    description = db.Column(db.Text, nullable=True)

    # Limits
    max_coupons = db.Column(db.Integer, default=20, nullable=False)  # Max coupons in this campaign

    # Validity
    starts_at = db.Column(db.DateTime, nullable=True)  # Optional start date
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional end date

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    business = db.relationship('Business', backref=db.backref('campaigns', lazy='dynamic'))
    created_by = db.relationship('User', backref='created_campaigns')

    __table_args__ = (
        db.Index('idx_campaigns_business', 'business_id'),
        db.Index('idx_campaigns_active', 'is_active'),
    )

    def get_coupons_count(self):
        """Get number of coupons in this campaign"""
        return Coupon.query.filter_by(campaign_id=self.id).count()

    def get_active_coupons_count(self):
        """Get number of active coupons in this campaign"""
        return Coupon.query.filter_by(
            campaign_id=self.id,
            is_active=True
        ).count()

    def can_add_coupon(self):
        """Check if campaign can have more coupons"""
        return self.get_coupons_count() < self.max_coupons

    def to_dict(self):
        """Convert campaign to dictionary"""
        return {
            'id': self.id,
            'business_id': self.business_id,
            'name': self.name,
            'description': self.description,
            'max_coupons': self.max_coupons,
            'coupons_count': self.get_coupons_count(),
            'active_coupons_count': self.get_active_coupons_count(),
            'can_add_coupon': self.can_add_coupon(),
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Coupon(db.Model):
    """Exclusive coupon template created by business or admin"""
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)  # Campaign this coupon belongs to
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)  # Optional specific store

    # Article info
    article_name = db.Column(db.String(200), nullable=False)  # "1kg Mljeveno meso"
    description = db.Column(db.Text, nullable=True)  # Additional description
    normal_price = db.Column(db.Float, nullable=False)  # 20.00 KM
    discount_percent = db.Column(db.Integer, nullable=False)  # 50
    quantity_description = db.Column(db.String(100), nullable=True)  # "1kg"
    image_path = db.Column(db.String, nullable=True)  # Coupon/product image

    # Availability
    total_quantity = db.Column(db.Integer, nullable=False)  # 5 coupons total
    remaining_quantity = db.Column(db.Integer, nullable=False)  # 3 remaining
    credits_cost = db.Column(db.Integer, default=20, nullable=False)  # 20 credits

    # Validity
    valid_days = db.Column(db.Integer, nullable=False)  # 1-10 days from purchase
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional hard expiration for entire coupon campaign

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    business = db.relationship('Business', backref=db.backref('coupons', lazy='dynamic'))
    campaign = db.relationship('Campaign', backref=db.backref('coupons', lazy='dynamic'))
    store = db.relationship('Store', backref=db.backref('coupons', lazy='dynamic'))
    created_by = db.relationship('User', backref='created_coupons')

    __table_args__ = (
        db.Index('idx_coupons_business', 'business_id'),
        db.Index('idx_coupons_campaign', 'campaign_id'),
        db.Index('idx_coupons_store', 'store_id'),
        db.Index('idx_coupons_active', 'is_active'),
    )

    @property
    def final_price(self):
        """Calculate final price after discount"""
        return round(self.normal_price * (1 - self.discount_percent / 100), 2)

    @property
    def savings(self):
        """Calculate savings amount"""
        return round(self.normal_price - self.final_price, 2)

    @property
    def is_sold_out(self):
        """Check if coupon is sold out"""
        return self.remaining_quantity <= 0


class UserCoupon(db.Model):
    """Purchased coupon by user"""
    __tablename__ = 'user_coupons'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Redemption
    redemption_code = db.Column(db.String(6), nullable=False, index=True)  # "847293"
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'redeemed', 'expired'

    # Dates
    purchased_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    redeemed_at = db.Column(db.DateTime, nullable=True)

    # Reminder tracking
    reminder_50_sent = db.Column(db.Boolean, default=False, nullable=False)
    reminder_final_sent = db.Column(db.Boolean, default=False, nullable=False)

    # Buyer rates business
    buyer_to_business_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    buyer_to_business_comment = db.Column(db.Text, nullable=True)
    buyer_product_review = db.Column(db.Text, nullable=True)  # Unlocks 24h after redemption
    buyer_review_unlocked_at = db.Column(db.DateTime, nullable=True)
    buyer_review_submitted_at = db.Column(db.DateTime, nullable=True)

    # Business rates buyer
    business_to_buyer_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    business_to_buyer_comment = db.Column(db.Text, nullable=True)

    # Relationships
    coupon = db.relationship('Coupon', backref=db.backref('user_coupons', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('purchased_coupons', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_coupons_user', 'user_id'),
        db.Index('idx_user_coupons_coupon', 'coupon_id'),
        db.Index('idx_user_coupons_status', 'status'),
        db.Index('idx_user_coupons_expires', 'expires_at'),
        db.Index('idx_user_coupons_code', 'redemption_code'),
    )

    @staticmethod
    def generate_redemption_code():
        """Generate a 6-digit redemption code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @property
    def is_expired(self):
        """Check if coupon has expired"""
        return datetime.now() > self.expires_at and self.status != 'redeemed'

    @property
    def can_submit_product_review(self):
        """Check if user can submit product review (24h after redemption)"""
        if not self.redeemed_at or self.buyer_product_review:
            return False
        return datetime.now() >= self.buyer_review_unlocked_at


class EmailEvent(db.Model):
    """Tracks email events from SendGrid webhook (opens, clicks, etc.)"""
    __tablename__ = 'email_events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # SendGrid event data
    email = db.Column(db.String, nullable=False, index=True)
    event_type = db.Column(db.String, nullable=False)  # 'open', 'click', 'delivered', 'bounce', etc.

    # User reference (if we can match the email)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Email metadata
    sg_message_id = db.Column(db.String, nullable=True)  # SendGrid message ID
    sg_event_id = db.Column(db.String, nullable=True, unique=True)  # Unique event ID to prevent duplicates

    # Click-specific data
    url = db.Column(db.String, nullable=True)  # URL clicked (for click events)

    # Additional metadata
    user_agent = db.Column(db.String, nullable=True)
    ip = db.Column(db.String, nullable=True)

    # Timestamps
    timestamp = db.Column(db.DateTime, nullable=False)  # When SendGrid recorded the event
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('email_events', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_email_events_email', 'email'),
        db.Index('idx_email_events_user', 'user_id'),
        db.Index('idx_email_events_type', 'event_type'),
        db.Index('idx_email_events_timestamp', 'timestamp'),
    )


class JobRun(db.Model):
    """Track scheduled job executions for monitoring and history"""
    __tablename__ = 'job_runs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_name = db.Column(db.String(100), nullable=False, index=True)  # 'product_scan', 'email_summary', etc.
    status = db.Column(db.String(20), nullable=False)  # 'started', 'completed', 'failed'
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)

    # Stats
    records_processed = db.Column(db.Integer, nullable=True)  # e.g., users scanned, emails sent
    records_success = db.Column(db.Integer, nullable=True)
    records_failed = db.Column(db.Integer, nullable=True)

    # Error tracking
    error_message = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.Index('idx_job_runs_name_started', 'job_name', 'started_at'),
    )

    @classmethod
    def start(cls, job_name: str):
        """Start tracking a new job run"""
        run = cls(job_name=job_name, status='started', started_at=datetime.now())
        db.session.add(run)
        db.session.commit()
        return run

    def complete(self, records_processed=None, records_success=None, records_failed=None):
        """Mark job as completed"""
        self.status = 'completed'
        self.completed_at = datetime.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.records_processed = records_processed
        self.records_success = records_success
        self.records_failed = records_failed
        db.session.commit()

    def fail(self, error_message: str):
        """Mark job as failed"""
        self.status = 'failed'
        self.completed_at = datetime.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.error_message = error_message
        db.session.commit()

    @classmethod
    def get_last_run(cls, job_name: str):
        """Get the most recent run for a job"""
        return cls.query.filter_by(job_name=job_name).order_by(cls.started_at.desc()).first()

    @classmethod
    def get_last_successful_run(cls, job_name: str):
        """Get the most recent successful run for a job"""
        return cls.query.filter_by(job_name=job_name, status='completed').order_by(cls.started_at.desc()).first()


class EmailNotification(db.Model):
    """Track all emails sent by the system"""
    __tablename__ = 'email_notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Who received it
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    email = db.Column(db.String, nullable=False, index=True)

    # What type of email
    email_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: 'daily_scan', 'weekly_summary', 'verification', 'welcome', 'password_reset',
    #        'coupon_purchase', 'coupon_reminder', 'coupon_expiry', 'bonus_credits', etc.

    # Subject and brief description
    subject = db.Column(db.String(500), nullable=True)

    # Status
    status = db.Column(db.String(20), nullable=False, default='sent')  # 'sent', 'failed', 'bounced'
    error_message = db.Column(db.Text, nullable=True)

    # Timing
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Optional extra data (JSON)
    extra_data = db.Column(db.JSON, nullable=True)  # e.g., {'products_found': 10, 'terms_count': 3}

    # Relationships
    user = db.relationship('User', backref=db.backref('email_notifications', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_email_notifications_type_sent', 'email_type', 'sent_at'),
        db.Index('idx_email_notifications_user_sent', 'user_id', 'sent_at'),
    )

    @classmethod
    def log_email(cls, email: str, email_type: str, subject: str = None,
                  user_id: str = None, status: str = 'sent',
                  error_message: str = None, extra_data: dict = None):
        """Log an email that was sent"""
        notification = cls(
            email=email,
            email_type=email_type,
            subject=subject,
            user_id=user_id,
            status=status,
            error_message=error_message,
            extra_data=extra_data,
            sent_at=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def get_user_email_history(cls, user_id: str, limit: int = 50):
        """Get email history for a user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.sent_at.desc()).limit(limit).all()

    @classmethod
    def get_recent_emails(cls, email_type: str = None, limit: int = 100):
        """Get recent emails, optionally filtered by type"""
        query = cls.query
        if email_type:
            query = query.filter_by(email_type=email_type)
        return query.order_by(cls.sent_at.desc()).limit(limit).all()


# ==================== SOCIAL MEDIA POSTS ====================

class SocialMediaPost(db.Model):
    """Scheduled social media posts for Facebook/Instagram"""
    __tablename__ = 'social_media_posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Schedule
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, published, failed, cancelled

    # Content
    content = db.Column(db.Text, nullable=False)  # Post text
    image_url = db.Column(db.String, nullable=True)  # Product image URL

    # Products snapshot (stored as JSON for historical accuracy)
    products_data = db.Column(JSON, nullable=False)  # [{id, title, store, base_price, discount_price, discount_pct, image}]

    # Publishing result
    published_at = db.Column(db.DateTime, nullable=True)
    facebook_post_id = db.Column(db.String, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.Index('idx_social_posts_scheduled', 'scheduled_time'),
        db.Index('idx_social_posts_status', 'status'),
    )

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status,
            'content': self.content,
            'image_url': self.image_url,
            'products': self.products_data,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'facebook_post_id': self.facebook_post_id,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserProductImage(db.Model):
    """User-uploaded product images for tracking/wish list"""
    __tablename__ = 'user_product_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    # Image storage
    image_url = db.Column(db.String, nullable=False)  # S3 URL
    thumbnail_url = db.Column(db.String, nullable=True)  # Resized version

    # Processing status: pending, processing, processed, failed
    status = db.Column(db.String, default='pending', nullable=False)

    # AI extraction results
    extracted_name = db.Column(db.String, nullable=True)  # Product name from AI
    extracted_price = db.Column(db.Numeric(10, 2), nullable=True)  # Price if visible
    extracted_data = db.Column(JSON, nullable=True)  # Full AI response

    # Matched product (if found in our database)
    matched_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)

    # User can add notes
    user_notes = db.Column(db.String, nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.now)
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('product_images', lazy='dynamic'))
    matched_product = db.relationship('Product', backref=db.backref('user_images', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_product_images_user', 'user_id'),
        db.Index('idx_user_product_images_status', 'status'),
    )

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'status': self.status,
            'extracted_name': self.extracted_name,
            'extracted_price': float(self.extracted_price) if self.extracted_price else None,
            'matched_product_id': self.matched_product_id,
            'user_notes': self.user_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


class CameraButtonAnalytics(db.Model):
    """Track user interactions with the floating camera button feature"""
    __tablename__ = 'camera_button_analytics'

    id = db.Column(db.Integer, primary_key=True)

    # User info (nullable for anonymous users)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)  # For anonymous tracking

    # Interaction tracking
    action = db.Column(db.String(50), nullable=False)  # 'button_click', 'expand', 'camera_click', 'gallery_click', 'upload_start', 'upload_complete', 'upload_cancel'

    # Context
    page_url = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    # For upload_complete actions, reference the uploaded image
    uploaded_image_id = db.Column(db.Integer, db.ForeignKey('user_product_images.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref='camera_analytics', lazy=True)
    uploaded_image = db.relationship('UserProductImage', backref='analytics_entry', lazy=True)

    __table_args__ = (
        db.Index('idx_camera_analytics_user', 'user_id'),
        db.Index('idx_camera_analytics_action', 'action'),
        db.Index('idx_camera_analytics_created', 'created_at'),
        db.Index('idx_camera_analytics_session', 'session_id'),
    )


class PwaInstallAnalytics(db.Model):
    """Track PWA install prompts and installations"""
    __tablename__ = 'pwa_install_analytics'

    id = db.Column(db.Integer, primary_key=True)

    # User info (nullable for anonymous users)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)  # For anonymous tracking

    # Event tracking
    # 'prompt_shown' - beforeinstallprompt fired
    # 'prompt_accepted' - user clicked install
    # 'prompt_dismissed' - user dismissed prompt
    # 'installed' - appinstalled event fired
    # 'standalone_launch' - app opened in standalone mode
    event = db.Column(db.String(50), nullable=False)

    # Context
    page_url = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # 'android', 'ios', 'desktop'
    browser = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref='pwa_analytics', lazy=True)

    __table_args__ = (
        db.Index('idx_pwa_analytics_user', 'user_id'),
        db.Index('idx_pwa_analytics_event', 'event'),
        db.Index('idx_pwa_analytics_created', 'created_at'),
        db.Index('idx_pwa_analytics_session', 'session_id'),
    )


# ==================== SUPPORT MESSAGES ====================

class SupportMessage(db.Model):
    """Support chat messages between admin and users.

    Used for:
    - Admin replies to user feedback
    - Proactive admin outreach to users
    - User responses to admin messages
    """
    __tablename__ = 'support_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # The user this conversation is with (NOT the admin)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Who sent this message: 'admin' or 'user'
    sender_type = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

    # For admin messages, track which admin sent it
    admin_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Message content
    message = db.Column(db.Text, nullable=False)

    # Optional reference to feedback this message is replying to
    feedback_id = db.Column(db.Integer, db.ForeignKey('user_feedback.id', ondelete='SET NULL'), nullable=True)

    # Read status
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Email notification status
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('support_messages', lazy='dynamic'))
    admin = db.relationship('User', foreign_keys=[admin_user_id])
    feedback = db.relationship('UserFeedback', backref=db.backref('support_messages', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_support_messages_user', 'user_id'),
        db.Index('idx_support_messages_created', 'created_at'),
        db.Index('idx_support_messages_unread', 'user_id', 'is_read'),
        db.Index('idx_support_messages_feedback', 'feedback_id'),
    )


class EmailAuthToken(db.Model):
    """Magic link tokens for email-based auto-login.

    When sending emails, we generate a unique token per user that allows
    one-click login when clicked from email clients that don't have the
    user's session (e.g., Gmail's embedded browser).
    """
    __tablename__ = 'email_auth_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Token validity
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)  # Set when token is consumed

    # Context - which email campaign generated this token
    email_type = db.Column(db.String(50), nullable=True)  # 'daily_summary', 'weekly_summary', etc.

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('email_auth_tokens', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_email_auth_token', 'token'),
        db.Index('idx_email_auth_user', 'user_id'),
        db.Index('idx_email_auth_expires', 'expires_at'),
    )

    @classmethod
    def generate_for_user(cls, user_id, email_type=None, hours_valid=72):
        """Generate a new magic link token for a user.

        Args:
            user_id: The user's ID
            email_type: Optional - the type of email (for analytics)
            hours_valid: How long the token is valid (default 72 hours)

        Returns:
            The token string (to be included in email links)
        """
        from datetime import timedelta

        token = secrets.token_urlsafe(32)  # 43 chars, URL-safe
        expires_at = datetime.now() + timedelta(hours=hours_valid)

        email_token = cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            email_type=email_type
        )
        db.session.add(email_token)
        db.session.commit()

        return token

    @classmethod
    def validate_and_consume(cls, token):
        """Validate a token and mark it as used.

        Args:
            token: The token string from the URL

        Returns:
            User object if valid, None if invalid/expired/used
        """
        email_token = cls.query.filter_by(token=token).first()

        if not email_token:
            return None

        # Check if already used
        if email_token.used_at:
            return None

        # Check if expired
        if datetime.now() > email_token.expires_at:
            return None

        # Mark as used
        email_token.used_at = datetime.now()
        db.session.commit()

        return email_token.user

    @classmethod
    def cleanup_expired(cls, days_old=7):
        """Delete expired tokens older than specified days."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days_old)
        cls.query.filter(cls.expires_at < cutoff).delete()
        db.session.commit()
