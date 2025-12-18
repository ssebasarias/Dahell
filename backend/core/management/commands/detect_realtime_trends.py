import logging
import torch
from django.core.management.base import BaseCommand
from django.db.models import F
from core.models import MarketIntelligenceLog, Category
from core.ai_utils import encode_text, encode_batch
from core.ai_classifier import classify_term # El Taxónomo
from pytrends.request import TrendReq
from sentence_transformers import util

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Phase 2.1 (PRO - V5): Semantic Radar + Taxonomy. Detects AND Classifies trends.'

    def handle(self, *args, **options):
        
        logger.info("📡 Scanning Real-Time Market Trends (Google Colombia)...")
        # Timeout aumentado para evitar errores de lectura
        pytrends = TrendReq(hl='es-CO', tz=300, timeout=(15,30)) 
        
        try:
            # 1. Obtener Tendencias Raw (Fallback a Realtime si Daily falla)
            # Usaremos Daily por defecto que es más estable para volúmenes altos
            try:
                trending_df = pytrends.trending_searches(pn='colombia')
                raw_trends = trending_df[0].tolist()
            except Exception:
                logger.warning("⚠️ Daily Trends failed. Switching to Realtime (Category-based)...")
                try:
                    df_realtime = pytrends.realtime_trending_searches(pn='CO')
                    raw_trends = df_realtime['title'].tolist()
                except Exception as e2:
                    logger.error(f"❌ Google Blocked us hard: {e2}")
                    # EMERGENCY FALLBACK: Simulación (solo dev)
                    raw_trends = ["Air Fryer Digital", "Tenis Running", "iPhone 15", "Elecciones Colombia"]
                    logger.warning(f"⚠️ Using Simulated Trends for DEV VALIDATION: {raw_trends}")

            logger.info(f"🔥 Radar Inputs ({len(raw_trends)}): {raw_trends[:5]}...")

            # 2. Cargar Anclas de Categorías DESDE LA DB
            logger.info("⚓ Loading Category Vectors from DB...")
            categories = list(Category.objects.exclude(embedding__isnull=True).values('id', 'name', 'embedding'))
            
            if not categories or len(categories) == 0:
                logger.warning("❌ No vectorized categories. We will proceed blind (Pure Classification).")
                cat_embeddings = None
            else:
                cat_embeddings = torch.tensor([c['embedding'] for c in categories])

            # 3. Procesamiento Semántico + Taxonómico
            logger.info("\n🤖 AI Contextual + Taxonomic Analysis:")
            logger.info("-" * 100)
            logger.info(f"{'TREND':<25} | {'MATCH':<20} | {'TAXONOMY':<15} | {'PARENT':<15}")
            logger.info("-" * 100)

            trend_embeddings = torch.tensor(encode_batch(raw_trends))

            # Si tenemos categorías, calculamos similitud
            if cat_embeddings is not None:
                cosine_scores = util.cos_sim(trend_embeddings, cat_embeddings)
            
            for i, trend in enumerate(raw_trends):
                matched_category_name = "New/Unknown"
                reliability = 0.0
                
                if cat_embeddings is not None:
                    scores = cosine_scores[i]
                    best_score, best_idx = torch.max(scores, dim=0)
                    reliability = best_score.item()
                    if reliability > 0.35:
                        matched_category_name = categories[best_idx.item()]['name']

                # --- El Taxónomo Entra en Acción ---
                # Clasificamos la tendencia independientemente de si hizo match
                # Esto nos permite descubrir NUEVOS Conceptos
                logger.info(f"   🤔 Classifying '{trend}'...")
                taxonomy_data = classify_term(trend) # Llama 3.1
                
                if not taxonomy_data:
                    logger.warning(f"   ⚠️ Classifier failed for {trend}")
                    continue
                
                tax_type = taxonomy_data.get('classification', 'UNKNOWN')
                parent = taxonomy_data.get('parent_industry', 'Unknown')
                
                # Reporte
                check_mark = "✅" if reliability > 0.35 else "🆕"
                logger.info(f"{trend[:25]:<25} | {matched_category_name[:20]:<20} | {tax_type:<15} | {parent[:15]} {check_mark}")

                # ACTION A: Si es un CONCEPTO o PRODUCTO válido, lo guardamos o actualizamos
                if tax_type in ['CONCEPT', 'PRODUCT']:
                    # Buscamos si ya existe como categoría o si es nueva
                    # Nota: Aquí podríamos decidir crear una nueva "Category" entry si no existe
                    # Para simplificar, si HIZO match fuerte, actualizamos esa categoría.
                    # Si NO hizo match (es nuevo), lo creamos como candidato nuevo.
                    
                    if reliability > 0.60:
                        # Actualizar categoría existente con datos taxonómicos si faltan
                        try:
                            cat_obj = Category.objects.get(name=matched_category_name)
                            if cat_obj.taxonomy_type == 'UNKNOWN':
                                cat_obj.taxonomy_type = tax_type
                                cat_obj.suggested_parent = parent
                                cat_obj.save()
                                logger.info(f"      📝 Updated taxonomy for {matched_category_name}")
                        except Category.DoesNotExist:
                            pass
                    
                    elif reliability < 0.40 and tax_type == 'CONCEPT':
                        # Oportunidad de Nuevo Nicho!
                        # Creamos una nueva entrada en Category para auditarla luego
                        new_cat, created = Category.objects.get_or_create(
                            name=trend,
                            defaults={
                                'description': f"Trend Concept automatically detected. Parent: {parent}",
                                'taxonomy_type': tax_type,
                                'suggested_parent': parent,
                                'intent_validation_status': 'PENDING' # Para que el Auditor lo revise
                            }
                        )
                        if created:
                            # Toca vectorizarla
                            new_cat.embedding = trend_embeddings[i].tolist()
                            new_cat.save()
                            logger.info(f"      ✨ NEW CONCEPT DISCOVERED: {trend} (Queued for Audit)")

                # Log Evidence
                MarketIntelligenceLog.objects.create(
                    source='semantic_radar_v5',
                    data_point=f'trend_{tax_type.lower()}',
                    value_text=f"{trend} -> {matched_category_name} (Tax: {tax_type})",
                    value_numeric=reliability,
                    embedding_context=trend_embeddings[i].tolist()
                )

        except Exception as e:
            logger.error(f"❌ Critical Error in Semantic Radar: {str(e)}")

