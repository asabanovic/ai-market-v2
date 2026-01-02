"""
Centralized configuration for user preference matching.

This module defines thresholds and settings used across the application
for matching products to user preferences (tracked products, email reports, etc.)
"""

# Minimum combined score (vector similarity + text bonus + context bonus) for a product
# to be considered a match for user preferences.
#
# The combined score includes:
# - Vector similarity: 0.0 - 1.0 (semantic similarity based on embeddings)
# - Text match bonus: +0.3 to +0.5 (for exact/partial text matches)
# - Context bonus: +0.0 to +0.2 (for products similar to user's favorites)
#
# A threshold of 0.7 (70%) ensures strong relevance to user preferences.
# Products scoring below this are filtered out.
PREFERENCE_MATCH_THRESHOLD = 0.7

# For display in frontend/emails (percentage format)
PREFERENCE_MATCH_THRESHOLD_PERCENT = int(PREFERENCE_MATCH_THRESHOLD * 100)  # 70%
