-- =======================================================================================
-- 🏗️ DB UPDATE V3: SOPORTE VECTORIAL TOTAL (CATEGORÍAS & EVENTOS)
-- =======================================================================================
-- Objetivo: Que Categorías, Eventos y Logs hablen el mismo idioma (Embeddings).
-- =======================================================================================

-- 1. VECTORIZAR CATEGORÍAS
-- Antes eran texto plano. Ahora tendrán cerebro semántico.
-- Usamos 384 dimensiones (estándar de 'all-MiniLM-L6-v2', rápido y bueno).
ALTER TABLE categories 
ADD COLUMN IF NOT EXISTS embedding vector(384),
ADD COLUMN IF NOT EXISTS description TEXT; -- Para darle más contexto al vectorizador

-- Índice HNSW para búsqueda ultrarrápida de categorías
CREATE INDEX IF NOT EXISTS idx_cat_embedding ON categories 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);


-- 2. VECTORIZAR EVENTOS (Calendario Inteligente)
-- Convertimos el MD (Markdown) en una tabla real y vectorizada.
CREATE TABLE IF NOT EXISTS future_events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- "Navidad", "Día Madre"
    date_start DATE NOT NULL,
    date_end DATE,
    prep_days INTEGER DEFAULT 30, -- Días de anticipación para avisar
    
    -- El Cerebro del Evento
    keywords TEXT, -- "juguetes, regalos, arbol" (Texto plano para referencia)
    embedding vector(384), -- Vector promedio de las keywords para búsqueda semántica
    
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_event_embedding ON future_events 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);


-- 3. LOGS CON CONTEXTO
-- Saber QUÉ vector generó este log para depurar
ALTER TABLE market_intelligence_logs
ADD COLUMN IF NOT EXISTS embedding_context vector(384); 

-- VACUUM ANALYZE eliminado para evitar errores de transaccion en pgAdmin.
-- Ejecutar manualmente si se desea: VACUUM ANALYZE;
