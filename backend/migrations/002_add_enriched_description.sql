-- Migration: Add enriched description to products
-- Description: Add a column for AI-enriched product descriptions
-- Date: 2025-11-12

-- Add enriched_description column to products table
ALTER TABLE products
ADD COLUMN IF NOT EXISTS enriched_description TEXT;

-- Add comment
COMMENT ON COLUMN products.enriched_description IS 'AI-generated rich description for better semantic search';
