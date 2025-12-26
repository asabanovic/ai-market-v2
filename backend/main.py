# Main entry point for the marketplace application
import os
from app import app, init_db
import routes  # noqa: F401

# Initialize and register AI agents (LangGraph-based)
from agents_api import agents_api_bp
from notifications_api import notifications_bp
from admin_credits_routes import admin_credits_bp
from admin_retention_routes import admin_retention_bp
from admin_social_routes import admin_social_bp
from sendgrid_webhook import sendgrid_webhook_bp
from coupon_routes import coupon_bp
from app import csrf

# Disable CSRF for agents API endpoints (JWT-based)
csrf.exempt(agents_api_bp)
csrf.exempt(notifications_bp)
csrf.exempt(admin_credits_bp)
csrf.exempt(admin_retention_bp)
csrf.exempt(admin_social_bp)
csrf.exempt(sendgrid_webhook_bp)
csrf.exempt(coupon_bp)

# Register API blueprints
app.register_blueprint(agents_api_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(admin_credits_bp)
app.register_blueprint(admin_retention_bp)
app.register_blueprint(admin_social_bp)
app.register_blueprint(sendgrid_webhook_bp)
app.register_blueprint(coupon_bp)

print("🤖 AI Agents System initialized (LangGraph with Supervisor)")
print("📧 SendGrid Webhook initialized")
print("🔔 Notifications API initialized")
print("💰 Admin Credits API initialized")
print("📊 Admin Retention API initialized")
print("📱 Social Media API initialized")
print("🎟️ Exclusive Coupons API initialized")

# Add helper functions to Jinja context after routes import
from routes import user_has_business_role

@app.context_processor
def inject_helper_functions():
    return dict(user_has_business_role=user_has_business_role)

if __name__ == "__main__":
    # Initialize database
    init_db()

    # Use debug mode only in development
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    # Port configuration
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
