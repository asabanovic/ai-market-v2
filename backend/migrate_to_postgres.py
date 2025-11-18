#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL with pgvector
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URLs
SQLITE_URL = os.environ.get("SQLITE_DATABASE_URL")
POSTGRES_URL = os.environ.get("DATABASE_URL")

print(f"Migrating from SQLite to PostgreSQL...")
print(f"SQLite: {SQLITE_URL}")
print(f"PostgreSQL: {POSTGRES_URL}")

# Create engines
sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

# First, create all tables in PostgreSQL using SQLAlchemy models
print("\n1. Creating PostgreSQL schema...")
from app import db, app
with app.app_context():
    # Import models to register them
    import models
    # Create all tables
    db.create_all()
    print("✓ Schema created successfully")

# Now migrate the data
print("\n2. Migrating data...")

# Get list of tables from SQLite
with sqlite_engine.connect() as sqlite_conn:
    result = sqlite_conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    tables = [row[0] for row in result]
    print(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")

# Migrate each table
for table_name in tables:
    print(f"\n  Migrating table: {table_name}")

    try:
        # Read data from SQLite
        with sqlite_engine.connect() as sqlite_conn:
            result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()

            if len(rows) == 0:
                print(f"    ✓ Table {table_name} is empty, skipping...")
                continue

            print(f"    Found {len(rows)} rows")

        # Insert data into PostgreSQL
        with postgres_engine.begin() as postgres_conn:
            # Build insert query
            column_names = ', '.join([f'"{col}"' for col in columns])
            placeholders = ', '.join([f':{col}' for col in columns])
            insert_query = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'

            # Insert rows
            for row in rows:
                row_dict = dict(zip(columns, row))
                try:
                    postgres_conn.execute(text(insert_query), row_dict)
                except Exception as e:
                    print(f"    ⚠ Error inserting row: {e}")
                    # Try to continue with next row
                    continue

            print(f"    ✓ Migrated {len(rows)} rows")

    except Exception as e:
        print(f"    ✗ Error migrating table {table_name}: {e}")
        continue

# Update sequences for PostgreSQL auto-increment columns
print("\n3. Updating PostgreSQL sequences...")
with postgres_engine.begin() as postgres_conn:
    # Get all sequences
    result = postgres_conn.execute(text("""
        SELECT sequence_name FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    """))
    sequences = [row[0] for row in result]

    for seq in sequences:
        # Extract table and column name from sequence name
        # Typical format: tablename_columnname_seq
        parts = seq.rsplit('_', 2)
        if len(parts) >= 2:
            table_name = parts[0]
            column_name = parts[1]

            try:
                # Get max value from table
                result = postgres_conn.execute(text(f'SELECT MAX("{column_name}") FROM {table_name}'))
                max_val = result.scalar()

                if max_val:
                    # Update sequence
                    postgres_conn.execute(text(f"SELECT setval('{seq}', {max_val})"))
                    print(f"  ✓ Updated sequence {seq} to {max_val}")
            except Exception as e:
                print(f"  ⚠ Could not update sequence {seq}: {e}")

print("\n✅ Migration completed successfully!")
print("\nNext steps:")
print("1. Verify the data in PostgreSQL")
print("2. Restart the Flask backend with: python3 main.py")
print("3. Test the application")
