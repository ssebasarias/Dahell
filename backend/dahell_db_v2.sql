-- =======================================================================================
-- 🏗️ ARQUITECTURA DE BASE DE DATOS: DAHELL INTELLIGENCE (V2.0 - REGLA DE ORO)
-- =======================================================================================
-- Objetivo: Soportar el ciclo completo "Dropi (Oferta) -> Trends/Shopify (Demanda) -> Decisión"
-- Optimizaciones incluidas:
-- 1. Control de Estado: Máquina de estados para tracking de análisis.
-- 2. Inteligencia de Mercado: Tablas para guardar datos de Google Trends y Shopify.
-- 3. Rendimiento: Índices optimizados para consultas masivas.
-- =======================================================================================

-- 1️⃣ ACTIVAR EXTENSIONES
CREATE EXTENSION IF NOT EXISTS vector;   -- IA
CREATE EXTENSION IF NOT EXISTS unaccent; -- Texto

-- =======================================================================================
-- 2️⃣ NIVEL DE INFRAESTRUCTURA (Proveedores y Bodegas)
-- =======================================================================================

CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id BIGINT PRIMARY KEY,
    city VARCHAR(100),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    store_name VARCHAR(255),
    plan_name VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    reputation_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =======================================================================================
-- 3️⃣ NIVEL DE PRODUCTO (La Oferta - Dropi)
-- =======================================================================================

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT PRIMARY KEY,
    supplier_id BIGINT REFERENCES suppliers(supplier_id),
    
    sku VARCHAR(100),
    title TEXT NOT NULL,
    description TEXT,
    
    sale_price NUMERIC(12, 2),      -- Costo Proveedor
    suggested_price NUMERIC(12, 2), -- Precio Sugerido (Dropi)
    profit_margin NUMERIC(12, 2) GENERATED ALWAYS AS (suggested_price - sale_price) STORED,
    
    product_type VARCHAR(50),
    url_image_s3 TEXT,
    
    -- Metadata de Rastreo (V2)
    source_platform VARCHAR(50) DEFAULT 'dropi', -- 'dropi', 'shopify', 'manual'
    last_seen_at TIMESTAMP DEFAULT NOW(),        -- Para detectar productos muertos
    raw_data JSONB DEFAULT '{}'::jsonb,          -- Datos extra flexibles
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_products_last_seen ON products(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_products_profit_created ON products (profit_margin DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_products_image_not_null ON products (product_id) WHERE url_image_s3 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_title_lower ON products ((lower(title)));


-- Relación Productos <-> Categorías
CREATE TABLE IF NOT EXISTS product_categories (
    product_id BIGINT REFERENCES products(product_id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

-- Histórico de Stock
CREATE TABLE IF NOT EXISTS product_stock_log (
    id SERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(product_id),
    warehouse_id BIGINT REFERENCES warehouses(warehouse_id),
    stock_qty INT NOT NULL,
    snapshot_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_log_product ON product_stock_log(product_id, snapshot_at DESC);


-- =======================================================================================
-- 4️⃣ NIVEL DE CLÚSTER & INTELIGENCIA (El Cerebro)
-- =======================================================================================

-- Tabla CALCULADA: Agrupa productos idénticos
CREATE TABLE IF NOT EXISTS unique_product_clusters (
    cluster_id BIGSERIAL PRIMARY KEY,
    representative_product_id BIGINT REFERENCES products(product_id),
    
    -- Métricas de Oferta (Internas)
    total_competitors INT DEFAULT 1,
    average_price NUMERIC(12,2),
    saturation_score VARCHAR(20),
    
    -- Identidad Humana (V2)
    concept_name VARCHAR(255), -- "Cepillo Secador OneStep"

    -- Máquina de Estados (V2 - Critical)
    analysis_level INTEGER DEFAULT 0, -- 0=Nuevo, 1=Trends Checked, 2=Shopify Checked, 3=Full Audit
    is_discarded BOOLEAN DEFAULT FALSE,
    discard_reason VARCHAR(255),
    is_candidate BOOLEAN DEFAULT FALSE, -- True = Pasó filtros básicos
    
    -- Inteligencia de Mercado - DEMANDA (V2)
    trend_score INTEGER DEFAULT 0, -- 0-100 (Google Trends)
    search_volume_estimate INTEGER,
    seasonality_flag VARCHAR(50), 
    
    -- Inteligencia de Mercado - REALIDAD (V2)
    market_avg_price DECIMAL(10,2), -- Precio real en Shopify
    potential_margin DECIMAL(10,2), -- (Market Price - Sale Price)
    market_saturation_level VARCHAR(20), -- "Blue Ocean", "Red Ocean"

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices V2 para gestión rápida
CREATE INDEX IF NOT EXISTS idx_cluster_analysis ON unique_product_clusters(analysis_level, is_candidate, is_discarded);
CREATE INDEX IF NOT EXISTS idx_clusters_competitors_price ON unique_product_clusters (total_competitors, average_price);


-- Relación Miembrsía (Qué producto pertenece a qué cluster)
CREATE TABLE IF NOT EXISTS product_cluster_membership (
    product_id BIGINT PRIMARY KEY REFERENCES products(product_id),
    cluster_id BIGINT REFERENCES unique_product_clusters(cluster_id),
    match_confidence DECIMAL(3,2),
    match_method VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_cluster_membership_composite ON product_cluster_membership (product_id, cluster_id);


-- Embeddings IA (Vectores)
CREATE TABLE IF NOT EXISTS product_embeddings (
    product_id BIGINT PRIMARY KEY REFERENCES products(product_id) ON DELETE CASCADE,
    embedding_visual vector(512),
    embedding_text vector(512),
    processed_at TIMESTAMP DEFAULT NOW()
);
-- Índices Vectoriales (HNSW)
CREATE INDEX IF NOT EXISTS idx_emb_visual ON product_embeddings USING hnsw (embedding_visual vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_emb_text ON product_embeddings USING hnsw (embedding_text vector_cosine_ops) WITH (m = 16, ef_construction = 64);


-- =======================================================================================
-- 5️⃣ AUDITORÍA & LOGS (La Evidencia)
-- =======================================================================================

-- Configuración Dinámica del Clusterizer
CREATE TABLE IF NOT EXISTS cluster_config (
    id SERIAL PRIMARY KEY,
    weight_visual FLOAT DEFAULT 0.6,
    weight_text FLOAT DEFAULT 0.4,
    threshold_visual_rescue FLOAT DEFAULT 0.15,
    threshold_text_rescue FLOAT DEFAULT 0.95,
    threshold_hybrid FLOAT DEFAULT 0.68,
    updated_at TIMESTAMP DEFAULT NOW(),
    version_note VARCHAR(100) DEFAULT 'Initial Config'
);

-- Feedback Humano (Entrenamiento)
CREATE TABLE IF NOT EXISTS ai_feedback (
    id SERIAL PRIMARY KEY,
    product_id BIGINT,
    candidate_id BIGINT,
    visual_score FLOAT,
    text_score FLOAT,
    final_score FLOAT,
    match_method VARCHAR(50),
    active_weights JSONB,
    decision VARCHAR(20),
    feedback VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON ai_feedback(created_at DESC);

-- Nueva Tabla: MARKET LOGS (V2)
-- Guarda la evidencia de Trends y Shopify para cada cluster
CREATE TABLE IF NOT EXISTS market_intelligence_logs (
    id SERIAL PRIMARY KEY,
    cluster_id BIGINT REFERENCES unique_product_clusters(cluster_id) ON DELETE CASCADE,
    source VARCHAR(50), -- "google_trends", "shopify_search"
    data_point VARCHAR(100), -- "trend_score", "competitor_price"
    value_text TEXT,
    value_numeric DECIMAL(10,2),
    snapshot_at TIMESTAMP DEFAULT NOW()
);


-- =======================================================================================
-- 6️⃣ DATOS SEMILLA (Inicialización)
-- =======================================================================================

INSERT INTO cluster_config (weight_visual, weight_text, threshold_visual_rescue, threshold_text_rescue, threshold_hybrid, version_note)
SELECT 0.6, 0.4, 0.15, 0.95, 0.68, 'Calibracion Base V2'
WHERE NOT EXISTS (SELECT 1 FROM cluster_config);

VACUUM ANALYZE;
