# Flask marketplace application with Replit Auth, PostgreSQL, OpenAI, and Infobip integration
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Load environment variables from .env file
load_dotenv()

# ---- LangSmith Tracing Config ----
# LangSmith will automatically enable tracing if these env vars are set
# See .env file for configuration
if os.environ.get("LANGSMITH_TRACING") == "true":
    logging.info(f"🔍 LangSmith tracing enabled for project: {os.environ.get('LANGSMITH_PROJECT', 'default')}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-change-in-production"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure CORS for frontend access
CORS(app,
     origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PATCH' ,'PUT', 'DELETE', 'OPTIONS'])

# Configure session for production OAuth
app.config["SESSION_COOKIE_SECURE"] = True  # Require HTTPS for cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent XSS
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Allow OAuth redirects
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

# Security check for production
if not os.environ.get("SESSION_SECRET"):
    logging.warning("SESSION_SECRET not set - using default (not secure for production)")

# Database configuration with SQLite fallback
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///marketplace.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Security configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token validity
# Disable CSRF for API endpoints (using JWT for security instead)
app.config['WTF_CSRF_ENABLED'] = False

# Initialize CSRF protection (disabled for JWT-based API)
csrf = CSRFProtect(app)

# Make CSRF token available in all templates
from flask_wtf.csrf import generate_csrf

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if value:
        try:
            import json
            return json.loads(value)
        except (ValueError, TypeError):
            return []
    return []

# Initialize database and create default data
def init_db():
    with app.app_context():
        # Import all models before creating tables
        import models

        try:
            db.create_all()
            logging.info("Database tables created")

            # Now import specific models for use
            from models import Package, User

            # Initialize default packages
            package_count = db.session.query(Package).count()
            logging.info(f"Found {package_count} packages in database")

            if package_count == 0:
                packages = [
                    Package(name='Free', daily_limit=10),
                    Package(name='Trial', daily_limit=50),
                    Package(name='Medium', daily_limit=30),
                    Package(name='Premium', daily_limit=100)
                ]
                for package in packages:
                    db.session.add(package)
                db.session.commit()
                logging.info("Default packages created")

            # Create admin account
            admin_email = "adnanxteam@gmail.com"
            admin_user = db.session.query(User).filter_by(email=admin_email).first()

            if not admin_user:
                # Create admin user
                from datetime import datetime
                admin_user = User(
                    id=str(datetime.now().timestamp()),
                    email=admin_email,
                    first_name="Admin",
                    last_name="User",
                    city="Tuzla",
                    is_verified=True,
                    is_admin=True,
                    package_id=1
                )
                db.session.add(admin_user)
                db.session.commit()
                logging.info(f"Admin account created for {admin_email}")
            else:
                # Make sure existing user is admin and verified
                admin_user.is_admin = True
                admin_user.is_verified = True
                db.session.commit()
                logging.info(f"Admin privileges updated for {admin_email}")

        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            # Continue anyway - database might already be initialized

# Note: Run via main.py, not directly