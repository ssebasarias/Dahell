-- =====================================================
-- CORRECCIÓN DE ESQUEMA: Ampliar VARCHAR restrictivos
-- =====================================================
-- RAZÓN: Campos con límite de 100/50 chars causan truncación
-- Los datos reales del scraper pueden exceder estos límites
-- =====================================================

-- 1. Ampliar campos en tabla SUPPLIERS
ALTER TABLE suppliers ALTER COLUMN name TYPE VARCHAR(255);
ALTER TABLE suppliers ALTER COLUMN store_name TYPE VARCHAR(255);
ALTER TABLE suppliers ALTER COLUMN plan_name TYPE VARCHAR(255);

-- 2. Ampliar campos en tabla PRODUCTS  
ALTER TABLE products ALTER COLUMN sku TYPE VARCHAR(255);
ALTER TABLE products ALTER COLUMN product_type TYPE VARCHAR(255);

-- Verificar cambios
SELECT table_name, column_name, character_maximum_length 
FROM information_schema.columns 
WHERE table_schema='public' 
  AND table_name IN ('products', 'suppliers')
  AND column_name IN ('sku', 'name', 'store_name', 'plan_name', 'product_type')
ORDER BY table_name, column_name;
