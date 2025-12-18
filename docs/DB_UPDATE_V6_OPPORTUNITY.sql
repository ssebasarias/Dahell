ALTER TABLE unique_product_clusters ADD COLUMN IF NOT EXISTS market_opportunity_score DECIMAL(5,2) DEFAULT 0.0;
ALTER TABLE unique_product_clusters ADD COLUMN IF NOT EXISTS taxonomy_type VARCHAR(50) DEFAULT 'UNKNOWN';
ALTER TABLE unique_product_clusters ADD COLUMN IF NOT EXISTS validation_log TEXT;
