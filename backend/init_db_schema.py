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
