"""Migration script to add user_ip, daily credits fields to the database."""

from app import app, db
from datetime import date
from sqlalchemy import text

def migrate():
    """Add new fields to users and user_searches tables."""
    with app.app_context():
        try:
            # Add user_ip field to user_searches table
            print("Adding user_ip field to user_searches table...")
            db.session.execute(text("""
                ALTER TABLE user_searches
                ADD COLUMN IF NOT EXISTS user_ip VARCHAR(50);
            """))
            db.session.commit()
            print("✓ Added user_ip field")

            # Add daily credits fields to users table
            print("Adding daily credits fields to users table...")
            db.session.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS daily_credits INTEGER DEFAULT 10;
            """))
            db.session.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS daily_credits_used INTEGER DEFAULT 0;
            """))
            db.session.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS daily_credits_reset_date DATE DEFAULT CURRENT_DATE;
            """))
            db.session.commit()
            print("✓ Added daily_credits, daily_credits_used, daily_credits_reset_date fields")

            # Update existing users to have default values
            print("Updating existing users with default credit values...")
            db.session.execute(text("""
                UPDATE users
                SET daily_credits = 10,
                    daily_credits_used = 0,
                    daily_credits_reset_date = CURRENT_DATE
                WHERE daily_credits IS NULL;
            """))
            db.session.commit()
            print("✓ Updated existing users")

            print("\n✅ Migration completed successfully!")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
