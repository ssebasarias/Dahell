-- -----------------------------------------------------------------------------
-- 🛠️ DAHELL INTELLIGENCE: ACTUALIZACIÓN ESTRUCTURAL (FASE 0)
-- -----------------------------------------------------------------------------
-- Objetivo: Dotar a la base de datos de "Memoria" y "Capacidad de Decisión".
-- Este script NO BORRA datos, solo agrega columnas de control.
-- -----------------------------------------------------------------------------

-- 1. ACTUALIZAR TABLA DE PRODUCTOS (El Soldado)
-- Necesitamos saber cuándo fue la última vez que lo vimos vivo y de dónde vino.
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50) DEFAULT 'dropi', -- dropi, shopify, amazon...
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS raw_data JSONB DEFAULT '{}'::jsonb; -- Para guardar meta-data flexible sin migrations

-- Indexar para búsquedas rápidas de "Lo nuevo"
CREATE INDEX IF NOT EXISTS idx_products_last_seen ON products(last_seen_at);


-- 2. ACTUALIZAR TABLA DE CLUSTERS (El Concepto / Cerebro)
-- Aquí es donde vive la inteligencia del negocio.
ALTER TABLE unique_product_clusters
-- Identidad Humana
ADD COLUMN IF NOT EXISTS concept_name VARCHAR(255), -- Ej: "Depiladora Laser IPL"

-- Máquina de Estados (Control de Flujo)
ADD COLUMN IF NOT EXISTS analysis_level INTEGER DEFAULT 0, -- 0=Nuevo, 1=Trends, 2=Shopify, 3=Auditado
ADD COLUMN IF NOT EXISTS is_discarded BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS discard_reason VARCHAR(255), -- Ej: "Tendencia muerta en Trends"
ADD COLUMN IF NOT EXISTS is_candidate BOOLEAN DEFAULT FALSE, -- True = Pasó a Fase 3

-- Inteligencia de Mercado (Fase 2 - Demanda)
ADD COLUMN IF NOT EXISTS trend_score INTEGER DEFAULT 0, -- 0-100 de Google Trends
ADD COLUMN IF NOT EXISTS search_volume_estimate INTEGER, -- Estimado de búsquedas mensuales
ADD COLUMN IF NOT EXISTS seasonality_flag VARCHAR(50), -- "Estable", "Navidad", "Verano"...

-- Inteligencia de Mercado (Fase 3 - Realidad / Shopify)
ADD COLUMN IF NOT EXISTS market_avg_price DECIMAL(10,2), -- Precio promedio en Shopify
ADD COLUMN IF NOT EXISTS potential_margin DECIMAL(10,2), -- (Market Price - Avg Supplier Price)
ADD COLUMN IF NOT EXISTS market_saturation_level VARCHAR(20); -- "Blue Ocean", "Red Ocean"

-- Indexar para sacar reportes rápidos
CREATE INDEX IF NOT EXISTS idx_cluster_analysis ON unique_product_clusters(analysis_level, is_candidate, is_discarded);


-- 3. NUEVA TABLA: MARKET_INTELLIGENCE_LOG (La Evidencia)
-- Para guardar cada chequeo que hacemos en Shopify o Google Trends (Auditoría)
CREATE TABLE IF NOT EXISTS market_intelligence_logs (
    id SERIAL PRIMARY KEY,
    cluster_id BIGINT REFERENCES unique_product_clusters(cluster_id) ON DELETE CASCADE,
    source VARCHAR(50), -- "google_trends", "shopify_search", "facebook_ads"
    data_point VARCHAR(100), -- "price", "search_volume", "ad_creative"
    value_text TEXT,
    value_numeric DECIMAL(10,2),
    snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comentario:
-- Con esto, ya no necesitas "recodrdar" qué hacías. 
-- El campo 'analysis_level' te dice exactamente qué paso sigue para cada producto.
