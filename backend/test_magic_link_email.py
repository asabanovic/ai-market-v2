#!/usr/bin/env python3
"""
Test script to send a daily summary email with magic link authentication.
Run from the backend directory: python test_magic_link_email.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User
from sendgrid_utils import send_scan_summary_email

def send_test_email():
    with app.app_context():
        # Find the user by email
        user = User.query.filter_by(email='adnanxteam@gmail.com').first()

        if not user:
            print("User not found: adnanxteam@gmail.com")
            return False

        print(f"Found user: {user.id} - {user.email}")

        # Create test summary data
        summary = {
            'total_products': 3,
            'new_products': 2,
            'new_discounts': 1,
            'terms': [
                {
                    'search_term': 'Milka čokolada',
                    'lowest_price': 2.99,
                    'lowest_store': 'Bingo',
                    'new_count': 1,
                    'best_saving': 1.50
                },
                {
                    'search_term': 'Coca-Cola 2L',
                    'lowest_price': 3.49,
                    'lowest_store': 'Konzum',
                    'new_count': 0,
                    'best_saving': 0.80
                },
                {
                    'search_term': 'Nutella 400g',
                    'lowest_price': 8.99,
                    'lowest_store': 'Robot',
                    'new_count': 1,
                    'best_saving': 2.00
                }
            ]
        }

        # Get user name
        user_name = user.name if hasattr(user, 'name') and user.name else 'Korisnik'

        print(f"Sending daily summary email with magic link to {user.email}...")
        print(f"User ID: {user.id}")

        # Send the email with user_id for magic link
        result = send_scan_summary_email(
            user_email=user.email,
            user_name=user_name,
            summary=summary,
            user_id=user.id  # This enables magic link authentication!
        )

        if result:
            print("✅ Email sent successfully!")
            print("Check your inbox and click the link in incognito mode to test auto-login.")
        else:
            print("❌ Failed to send email")

        return result

if __name__ == '__main__':
    send_test_email()
