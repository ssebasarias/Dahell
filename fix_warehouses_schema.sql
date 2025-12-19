-- =====================================================
-- CORRECCIÓN DE ESQUEMA: Eliminar columna city de warehouses
-- =====================================================
-- RAZÓN: La columna city no puede ser recuperada de los datos JSON
-- del scraper. Solo tenemos warehouse_id disponible consistentemente.
-- =====================================================

-- 1. Eliminar columna city de la tabla warehouses
ALTER TABLE warehouses DROP COLUMN IF EXISTS city;

-- 2. Verificar estructura resultante
\d warehouses;

-- 3. Verificar conteo actual de warehouses
SELECT COUNT(*) as total_warehouses FROM warehouses;
