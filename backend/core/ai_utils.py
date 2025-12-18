import logging
import torch
from sentence_transformers import SentenceTransformer

# Singleton Pattern para cargar el modelo solo una vez en memoria
_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        # Usamos 'all-MiniLM-L6-v2' (o multilingual)
        # Es muy rápido y genera vectores de dimensión 384 (compatible con nuestra DB)
        logging.info("🧠 Loading Unified AI Brain (MiniLM-L6-v2)...")
        _model_instance = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', cache_folder='/app/cache_huggingface')
    return _model_instance

def encode_text(text):
    """
    Convierte cualquier texto (Categoría, Evento, Tendencia) en un Vector.
    Retorna: Lista de floats (embedding) lista para guardar en pgvector.
    """
    if not text:
        return None
    
    model = get_model()
    # Convert to tensor then to list for DB insertion
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()

def encode_batch(texts):
    """Para procesar listas grandes de una sola vez."""
    if not texts:
        return []
    model = get_model()
    embeddings = model.encode(texts, convert_to_tensor=False)
    return embeddings.tolist()

def get_image_embedding(image_path):
    """
    Legacy/Placeholder para compatibilidad.
    TODO: Implementar CLIP real si necesitamos search visual.
    """
    logging.warning("⚠️ get_image_embedding called but CLIP not loaded. Returning zeros.")
    return [0.0] * 384
