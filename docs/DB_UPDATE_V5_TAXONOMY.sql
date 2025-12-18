-- DB UPDATE V5: TAXONOMY (El Orden del Caos)
-- Objetivo: Diferenciar entre Industria, Concepto y Producto para aplicar la estrategia correcta.

ALTER TABLE categories
ADD COLUMN IF NOT EXISTS taxonomy_type VARCHAR(50) DEFAULT 'UNKNOWN'; 
-- Valores esperados: 'INDUSTRY', 'CONCEPT', 'PRODUCT', 'UNKNOWN'

ALTER TABLE categories
ADD COLUMN IF NOT EXISTS suggested_parent VARCHAR(100); 
-- Para organizar jerarquía (ej: 'Labial' -> Parent: 'Belleza')

-- Índice para filtrar rápido por tipo (ej: "Dame solo Conceptos para validar en ML")
CREATE INDEX idx_categories_taxonomy ON categories(taxonomy_type);
