#!/usr/bin/env python3
"""Test script for activation email (for users without tracked products)"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from sendgrid_utils import send_activation_email

with app.app_context():
    # Test with realistic example data
    test_savings = {
        'avg_weekly_savings': 15.75,
        'top_category': 'Mlijeko',
        'example_products': [
            {'name': 'Meggle Mlijeko 2.8% 1L', 'store': 'Bingo', 'saving': 0.65, 'percent': 26},
            {'name': 'Grand Kafa Gold 200g', 'store': 'Konzum', 'saving': 1.91, 'percent': 21},
            {'name': 'Nutella 400g', 'store': 'Mercator', 'saving': 2.51, 'percent': 20},
        ]
    }

    result = send_activation_email(
        user_email='adnanxteam@gmail.com',
        user_name='Adnan',
        example_savings=test_savings
    )

    print(f"Activation email sent: {result}")
