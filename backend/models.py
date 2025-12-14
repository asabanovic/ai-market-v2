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
    city = db.Column(db.String, nullable=True)
    preferences = db.Column(JSON, nullable=True)  # JSON field for user preferences
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), default=1)
    
    # Email verification fields
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
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

    # Weekly credits system - Two buckets:
    # 1. Regular credits: 40 credits per week (reset every Monday, never exceed 40)
    weekly_credits = db.Column(db.Integer, default=40)  # Regular credits (reset weekly)
    weekly_credits_used = db.Column(db.Integer, default=0)
    weekly_credits_reset_date = db.Column(db.Date, default=date.today)

    # 2. Extra credits: Earned credits (referrals, purchases) - these accumulate
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

    # Relationships
    package = db.relationship('Package', backref='users')
    searches = db.relationship('UserSearch', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    shopping_lists = db.relationship('ShoppingList', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    credit_transactions = db.relationship('CreditTransaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
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

# User searches table for tracking
class UserSearch(db.Model):
    __tablename__ = 'user_searches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)  # Allow null for anonymous searches
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
    referrer_code = db.Column(db.String(20), db.ForeignKey('users.referral_code'), nullable=False)  # Who referred
    referred_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)  # Who was referred
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
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    invited_by_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    redeemed_by_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=True)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String, nullable=False)  # 'discount_alert', 'price_drop', etc.
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
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

    # Search parameters used
    similarity_threshold = db.Column(db.Float, nullable=True)
    k = db.Column(db.Integer, nullable=True)

    # Results summary
    result_count = db.Column(db.Integer, nullable=False)
    total_before_filter = db.Column(db.Integer, nullable=True)

    # Detailed results with scores (JSON array)
    # Each item: {product_id, title, similarity, vector_score, text_score, rank}
    results_detail = db.Column(JSON, nullable=True)

    # Parsed query info from LLM (if any)
    parsed_query = db.Column(JSON, nullable=True)  # The search_items from parser

    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_search_logs_query', 'query'),
        db.Index('idx_search_logs_created_at', 'created_at'),
    )


# ==================== USER ACTIVITY TRACKING ====================

# UserActivity - detailed event logging for user interactions
class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)  # The date of the visit

    # Track first and last activity time on that day
    first_seen = db.Column(db.DateTime, default=datetime.now)
    last_seen = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Count of page views on that day (optional, for extra insight)
    page_views = db.Column(db.Integer, default=1)

    # Relationships
    user = db.relationship('User', backref=db.backref('daily_visits', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'visit_date', name='uq_user_daily_visit'),
        db.Index('idx_user_daily_visits_user_id', 'user_id'),
        db.Index('idx_user_daily_visits_date', 'visit_date'),
        db.Index('idx_user_daily_visits_user_date', 'user_id', 'visit_date'),
    )


# UserLogin - dedicated table for login history
class UserLogin(db.Model):
    __tablename__ = 'user_logins'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

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
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)

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