#!/usr/bin/env python3
"""Quick script to update user password"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(email='adnanxteam@gmail.com').first()

    if user:
        user.password_hash = generate_password_hash('demo123')
        db.session.commit()
        print(f"✓ Password updated for {user.email}")
        print(f"  Admin: {user.is_admin}")
        print(f"  ID: {user.id}")
    else:
        print("✗ User not found")
