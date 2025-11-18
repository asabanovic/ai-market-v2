#!/usr/bin/env python3
"""
Set password for admin user
"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(email='adnanxteam@gmail.com').first()
    if user:
        user.password_hash = generate_password_hash('admin123')
        db.session.commit()
        print(f"✅ Password set for {user.email}")
        print(f"   Email: adnanxteam@gmail.com")
        print(f"   Password: admin123")
    else:
        print("❌ User not found")
