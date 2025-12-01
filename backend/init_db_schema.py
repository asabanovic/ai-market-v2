#!/usr/bin/env python3
"""
Initialize database schema before running Alembic migrations.

This script creates all base tables defined in SQLAlchemy models
that Alembic migrations depend on. It must be run BEFORE alembic upgrade.

The Alembic migrations assume that base tables (users, products, businesses)
already exist because they add columns and create related tables.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def init_schema():
    """Initialize the database schema by creating all tables from SQLAlchemy models."""
    # Import app and db from the application
    from app import app, db

    with app.app_context():
        # Import all models so they're registered with SQLAlchemy
        import models

        try:
            # Enable pgvector extension for embeddings (if using PostgreSQL)
            db.session.execute(db.text('CREATE EXTENSION IF NOT EXISTS vector'))
            db.session.commit()
            logger.info("pgvector extension enabled (or already exists)")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension (may not be needed): {e}")
            db.session.rollback()

        # Create all tables
        db.create_all()
        logger.info("Database schema initialized successfully")

        # Seed default packages if they don't exist
        from models import Package, User
        package_count = db.session.query(Package).count()
        logger.info(f"Found {package_count} packages in database")

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
            logger.info("Default packages seeded successfully")

        # Ensure admin account exists and has admin privileges
        admin_email = os.environ.get('ADMIN_EMAIL', 'adnanxteam@gmail.com')
        admin_user = db.session.query(User).filter_by(email=admin_email).first()

        if not admin_user:
            # Create admin user
            from datetime import datetime
            from werkzeug.security import generate_password_hash
            admin_password = os.environ.get('ADMIN_PASSWORD')
            admin_user = User(
                id=str(datetime.now().timestamp()),
                email=admin_email,
                first_name="Admin",
                last_name="User",
                city="Tuzla",
                is_verified=True,
                is_admin=True,
                package_id=1,
                password_hash=generate_password_hash(admin_password) if admin_password else None
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Admin account created for {admin_email}")
        else:
            # Make sure existing user is admin and verified
            if not admin_user.is_admin or not admin_user.is_verified:
                admin_user.is_admin = True
                admin_user.is_verified = True
                db.session.commit()
                logger.info(f"Admin privileges updated for {admin_email}")
            else:
                logger.info(f"Admin account already configured for {admin_email}")

        # Verify key tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        required_tables = ['users', 'products', 'businesses']
        missing = [t for t in required_tables if t not in tables]

        if missing:
            logger.error(f"Missing required tables: {missing}")
            sys.exit(1)
        else:
            logger.info(f"Verified required tables exist: {required_tables}")
            logger.info(f"All tables in database: {tables}")

if __name__ == '__main__':
    logger.info("Initializing database schema...")
    init_schema()
    logger.info("Schema initialization complete")
