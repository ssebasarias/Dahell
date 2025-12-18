-- DB UPDATE V4: MARKET INTENT (La prueba de fuego)
-- Objetivo: Almacenar texto real de usuarios (Reviews/Preguntas) para validación semántica.
-- No guardamos precios, ni estrellas, ni ventas. Solo la voz del usuario.

CREATE TABLE IF NOT EXISTS marketplace_feedback (
    id BIGSERIAL PRIMARY KEY,
    
    -- Relación con la Categoría que estamos validando
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    
    -- Fuente del 'Sabor' (Amazon, MercadoLibre, Etsy)
    marketplace VARCHAR(50) NOT NULL, 
    
    -- Tipo de Feedback (Review, Pregunta, Comentario)
    feedback_type VARCHAR(20) NOT NULL, -- 'review', 'question', 'complaint'
    
    -- El Oro Puro: Lo que la gente dijo en realidad
    text_content TEXT NOT NULL,
    
    -- Vectorización del texto (Para medir coherencia semántica)
    embedding vector(384),
    
    -- Metadatos mínimos requeridos por el usuario
    posted_at DATE, -- Timestamp original del comentario (si existe)
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Índice para búsquedas rápidas por categoría
CREATE INDEX idx_marketplace_feedback_category ON marketplace_feedback(category_id);

-- Índice vectorial por si queremos buscar "quejas similares"
CREATE INDEX idx_marketplace_feedback_embedding ON marketplace_feedback USING hnsw (embedding vector_l2_ops);

-- Agregar columnas de métrica de calidad a la tabla CATEGORIAS
-- Para no tener que recalcular la coherencia cada vez
ALTER TABLE categories
ADD COLUMN IF NOT EXISTS semantic_coherence_score NUMERIC(5,2) DEFAULT 0.0, -- 0.0 a 1.0 (Qué tan denso es el cluster de reviews)
ADD COLUMN IF NOT EXISTS intent_validation_status VARCHAR(50) DEFAULT 'PENDING'; -- 'PENDING', 'VALIDATED', 'REJECTED_NOISE'
