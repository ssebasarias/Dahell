ALTER TABLE products
ADD COLUMN IF NOT EXISTS taxonomy_concept VARCHAR(255),
ADD COLUMN IF NOT EXISTS taxonomy_industry VARCHAR(255),
ADD COLUMN IF NOT EXISTS taxonomy_level VARCHAR(50);
-- concept: "Silla Gamer", industry: "Muebles", level: "CONCEPT"

CREATE INDEX IF NOT EXISTS idx_products_taxonomy_concept ON products(taxonomy_concept);
