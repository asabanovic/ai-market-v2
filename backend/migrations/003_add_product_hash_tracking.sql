-- Migration: Add hash tracking for products
-- Description: Add content_hash to products and product_embeddings for change detection
-- Date: 2025-11-12

-- Enable pgcrypto extension for hash functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add content_hash column to products table
-- This hash is computed from all important product fields used for presentation
ALTER TABLE products
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

-- Add content_hash column to product_embeddings table
-- This stores the hash of the product data that was used to generate the embedding
ALTER TABLE product_embeddings
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

-- Create index on content_hash for faster lookups
CREATE INDEX IF NOT EXISTS products_content_hash_idx ON products(content_hash);
CREATE INDEX IF NOT EXISTS product_embeddings_content_hash_idx ON product_embeddings(content_hash);

-- Create function to compute product content hash
-- This function computes SHA256 hash from important product fields
CREATE OR REPLACE FUNCTION compute_product_hash(
    p_title VARCHAR,
    p_enriched_description TEXT,
    p_category VARCHAR,
    p_base_price DOUBLE PRECISION,
    p_discount_price DOUBLE PRECISION,
    p_city VARCHAR,
    p_tags JSON
) RETURNS VARCHAR(64) AS $$
BEGIN
    -- Combine all important fields and compute SHA256 hash
    -- Use COALESCE to handle NULL values
    RETURN encode(
        digest(
            COALESCE(p_title, '') || '|' ||
            COALESCE(p_enriched_description, '') || '|' ||
            COALESCE(p_category, '') || '|' ||
            COALESCE(p_base_price::TEXT, '') || '|' ||
            COALESCE(p_discount_price::TEXT, '') || '|' ||
            COALESCE(p_city, '') || '|' ||
            COALESCE(p_tags::TEXT, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create trigger function to automatically update content_hash
CREATE OR REPLACE FUNCTION update_product_content_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_hash = compute_product_hash(
        NEW.title,
        NEW.enriched_description,
        NEW.category,
        NEW.base_price,
        NEW.discount_price,
        NEW.city,
        NEW.tags
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update content_hash on INSERT or UPDATE
DROP TRIGGER IF EXISTS products_content_hash_trigger ON products;
CREATE TRIGGER products_content_hash_trigger
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_content_hash();

-- Backfill content_hash for existing products
UPDATE products
SET content_hash = compute_product_hash(
    title,
    enriched_description,
    category,
    base_price,
    discount_price,
    city,
    tags
)
WHERE content_hash IS NULL;

-- Add comments
COMMENT ON COLUMN products.content_hash IS 'SHA256 hash of product content fields for change detection';
COMMENT ON COLUMN product_embeddings.content_hash IS 'Hash of the product content that was used to generate this embedding';
COMMENT ON FUNCTION compute_product_hash IS 'Computes SHA256 hash from important product fields';
