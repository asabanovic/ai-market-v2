-- Migration: Add notification preferences to users
-- Description: Track user notification settings (none, favorites, all)
-- Date: 2025-11-17

ALTER TABLE users
ADD COLUMN IF NOT EXISTS notification_preferences VARCHAR NULL DEFAULT 'none';

