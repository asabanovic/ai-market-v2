-- Migration: Create product_embeddings table
-- Description: Separate table for storing product vector embeddings
-- Date: 2025-11-12

-- Ensure pgvector extension is installed
CREATE EXTENSION IF NOT EXISTS vector;

-- Create product_embeddings table
CREATE TABLE IF NOT EXISTS product_embeddings (
    product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    embedding_text TEXT,  -- The text that was used to generate the embedding
    model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search using cosine distance
CREATE INDEX IF NOT EXISTS product_embeddings_vector_idx
ON product_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index on product_id for faster joins
CREATE INDEX IF NOT EXISTS product_embeddings_product_id_idx
ON product_embeddings(product_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_product_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER product_embeddings_updated_at
    BEFORE UPDATE ON product_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_product_embeddings_updated_at();

-- Add comment to table
COMMENT ON TABLE product_embeddings IS 'Stores vector embeddings for semantic search of products';
COMMENT ON COLUMN product_embeddings.embedding IS '1536-dimensional vector from OpenAI text-embedding-3-small';
COMMENT ON COLUMN product_embeddings.embedding_text IS 'The enriched text used to generate the embedding';
