#!/usr/bin/env python3
"""Test script for weekly summary email"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from sendgrid_utils import send_weekly_summary_email

with app.app_context():
    # Test data with various scenarios
    test_summary = {
        'total_products': 3,  # < 5 to trigger expansion CTA
        'total_matches': 12,
        'total_savings': 8.50,  # < 10 KM to trigger reframing
        'max_price_diff_percent': 42,
        'best_value_category': 'Mlijeko',
        'category_insights': [
            {'term': 'Mlijeko', 'price_diff_percent': 42},
            {'term': 'Kafa', 'price_diff_percent': 35},
        ],
        'best_deals': [
            {
                'product': 'Meggle Mlijeko 2.8% 1L',
                'store': 'Bingo',
                'original_price': 2.50,
                'discount_price': 1.85,
                'savings_percent': 26,
                'savings_amount': 0.65
            },
            {
                'product': 'Grand Kafa Gold 200g',
                'store': 'Konzum',
                'original_price': 8.90,
                'discount_price': 6.99,
                'savings_percent': 21,
                'savings_amount': 1.91
            },
            {
                'product': 'Nutella 400g',
                'store': 'Mercator',
                'original_price': 12.50,
                'discount_price': 9.99,
                'savings_percent': 20,
                'savings_amount': 2.51
            }
        ],
        'tracked_items': [
            {'product': '[Mlijeko] Meggle 2.8% 1L', 'store': 'Bingo', 'current_price': 1.85, 'price_change': -0.15},
            {'product': '[Mlijeko] Dukat 2.8% 1L', 'store': 'Konzum', 'current_price': 2.10, 'price_change': 0},
            {'product': '[Kafa] Grand Gold 200g', 'store': 'Konzum', 'current_price': 6.99, 'price_change': -0.50},
            {'product': '[Kafa] Doncafe 200g', 'store': 'Bingo', 'current_price': 7.50, 'price_change': 0},
            {'product': '[Nutella] Nutella 400g', 'store': 'Mercator', 'current_price': 9.99, 'price_change': -1.00},
        ],
        'price_drops': [
            {'product': 'Meggle Mlijeko 2.8% 1L', 'store': 'Bingo', 'drop_amount': 0.65},
            {'product': 'Grand Kafa Gold 200g', 'store': 'Konzum', 'drop_amount': 1.91},
        ],
        'new_products': [
            {'product': 'Nutella 400g (nova akcija)', 'store': 'Mercator', 'price': 9.99},
        ],
        'hero_deal': None  # No hero deal to test reframing
    }

    result = send_weekly_summary_email(
        user_email='adnanxteam@gmail.com',
        user_name='Adnan',
        summary=test_summary
    )

    print(f"Email sent: {result}")
