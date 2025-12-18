import logging
import requests
import numpy as np
import torch
from django.core.management.base import BaseCommand
from core.models import Category, MarketplaceFeedback, MarketIntelligenceLog
from core.ai_utils import encode_text, encode_batch

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Phase 4 (V5): Marketplace Intent Validation. Audits concepts using real user feedback based on Taxonomy.'

    def handle(self, *args, **options):
        logger.info("🕵️ Starting Marketplace Intent Audit (Taxonomy Aware)...")
        
        # 1. Seleccionar CONCEPTOS o PRODUCTOS pendientes de validación
        # Ignoramos 'INDUSTRY' (muy amplio) y 'UNKNOWN' (riesgoso)
        candidates = Category.objects.filter(
            intent_validation_status='PENDING',
            taxonomy_type__in=['CONCEPT', 'PRODUCT']
        )[:5] # Lote pequeño
        
        if not candidates.exists():
            logger.info("✨ No pending concepts/products to validate.")
            # Opcional: Podríamos reintentar con UNKNOWN si queremos ser agresivos
            return

        for cat in candidates:
            logger.info(f"\n🔬 Auditing {cat.taxonomy_type}: '{cat.name}'")
            
            collected_texts = []
            
            # A. MercadoLibre (Fuente Principal Colombia)
            ml_texts = self.fetch_mercadolibre_voice(cat.name)
            collected_texts.extend(ml_texts)
            
            # B. Amazon (Reviews Internacionales - Placeholder)
            # az_texts = self.fetch_amazon_voice(cat.name)
            # collected_texts.extend(az_texts)
            
            if not collected_texts:
                logger.warning(f"   ❌ Silence in the market. No feedback found for '{cat.name}'.")
                # Si es un producto muy nuevo, quizás no haya reviews.
                # Lo marcamos como 'NO_DATA' temporalmente
                cat.intent_validation_status = 'NO_DATA'
                cat.save()
                continue
                
            # C. Guardar y Vectorizar
            embeddings = encode_batch(collected_texts)
            
            # Guardamos en DB para auditoría futura
            for text, vector in zip(collected_texts, embeddings):
                MarketplaceFeedback.objects.create(
                    category=cat,
                    marketplace='mercadolibre_co', # Dinámico si usáramos varios
                    feedback_type='question_sample', 
                    text_content=text,
                    embedding=vector
                )
                
            # D. Análisis de Coherencia Semántica
            coherence_score = self.measure_semantic_coherence(embeddings)
            
            logger.info(f"   🧠 Semantic Coherence: {coherence_score:.2f} / 1.0")
            
            # E. Veredicto
            # Umbral ajustado: Si es un concepto, esperamos cierta variedad, si es producto, mucha repetición.
            threshold = 0.60 if cat.taxonomy_type == 'CONCEPT' else 0.70
            
            if coherence_score > threshold:
                cat.intent_validation_status = 'VALIDATED'
                logger.info("   ✅ PASS: Validated Market Intent.")
            elif coherence_score < 0.35:
                cat.intent_validation_status = 'REJECTED_NOISE'
                logger.info("   ⛔ FAIL: Semantically scattered (Ambiguous).")
            else:
                cat.intent_validation_status = 'UNCERTAIN'
                logger.info("   ⚠️ WARN: Mixed signals.")
                
            cat.semantic_coherence_score = coherence_score
            cat.save()

    def fetch_mercadolibre_voice(self, query):
        """
        Extrae preguntas reales de usuarios de los top posts de MercadoLibre.
        """
        try:
            # 1. Buscar Items Top por relevancia
            search_url = f"https://api.mercadolibre.com/sites/MCO/search?q={query}&limit=3"
            resp = requests.get(search_url).json()
            
            items = resp.get('results', [])
            if not items: return []
            
            collected = []
            
            # 2. De cada item, extraer preguntas
            for item in items:
                item_id = item['id']
                questions_url = f"https://api.mercadolibre.com/questions/search?item_id={item_id}&limit=5"
                q_resp = requests.get(questions_url).json()
                questions = q_resp.get('questions', [])
                
                for q in questions:
                    text = q.get('text', '').lower()
                    # Filtros anti-ruido
                    if len(text) > 10 and "precio" not in text and "disponible" not in text and "original" not in text:
                         collected.append(text)
            
            logger.info(f"   🗣️ ML: Captured {len(collected)} clean questions.")
            return collected
            
        except Exception as e:
            logger.error(f"   ❌ ML Scraper Error: {e}")
            return []

    def fetch_amazon_voice(self, query):
        """
        Placeholder para Amazon.
        Requiere Scraper API o Selenium pesado por bloqueo de bots.
        """
        # TODO: Implementar integración con ScraperAPI o similar.
        return []

    def measure_semantic_coherence(self, embeddings_list):
        if not embeddings_list: return 0.0
        tensor_matrix = torch.tensor(embeddings_list)
        centroid = torch.mean(tensor_matrix, dim=0)
        from torch.nn.functional import cosine_similarity
        similarities = cosine_similarity(tensor_matrix, centroid.unsqueeze(0))
        return torch.mean(similarities).item()
