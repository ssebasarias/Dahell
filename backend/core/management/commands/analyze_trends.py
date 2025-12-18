import time
import random
import logging
import datetime
from django.core.management.base import BaseCommand
from core.models import UniqueProductCluster, MarketIntelligenceLog, Category
from core.ai_utils import encode_text
from pytrends.request import TrendReq

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Phase 2 (V3): Strategic Trend Analysis. Analyzes Category Health first, then filters Products.'

    def handle(self, *args, **options):
        logger.info("🕵️ Starting Strategic Market Analysis (Category First)...")
        
        # 1. Obtener Categorías para analizar
        # Idealmente, analizamos las que no se han chequeado en X días.
        categories = Category.objects.all()
        
        if not categories.exists():
            logger.warning("⚠️ No Categories found in DB. Please run 'seed_vectors' or 'loader' first.")
            return

        pytrends = TrendReq(hl='es-CO', tz=300, timeout=(10,25))
        
        for category in categories:
            try:
                logger.info(f"\n📊 Analyzing Category Health: '{category.name}'")
                
                # 2. Consultar Histórico de la Categoría (12 meses)
                # Usamos el nombre de la categoría como keyword principal
                kw = category.name
                pytrends.build_payload([kw], cat=0, timeframe='today 12-m', geo='CO', gprop='')
                interest_df = pytrends.interest_over_time()
                
                if interest_df.empty:
                    logger.warning(f"   📉 Dead Category? No data for '{kw}'.")
                    self.mark_category_status(category, "DEAD", 0)
                    continue

                # 3. Diagnóstico de Salud de Categoría
                avg_interest = interest_df[kw].mean()
                trend_status = self.diagnose_trend(interest_df[kw]) # Rising/Falling/Stable
                
                logger.info(f"   => Score: {avg_interest:.1f} | Status: {trend_status}")

                # 4. Acción Estratégica
                if avg_interest < 15:
                    logger.info("   ❄️ Category is COLD. putting products to sleep.")
                    self.perform_mass_action(category, "SLEEP")
                elif trend_status == "FALLING 📉":
                     logger.info("   ⚠️ Category is DECLINING. Be cautious.")
                     # Aún mantenemos productos pero con flag de alerta
                     self.perform_mass_action(category, "CAUTION")
                else:
                    logger.info("   🔥 Category is HEALTHY/HOT! waking up candidates.")
                    self.perform_mass_action(category, "WAKE_UP")

                # 5. Log de Inteligencia (Vectorizado)
                MarketIntelligenceLog.objects.create(
                    cluster=None,
                    source='strategic_analysis',
                    data_point='category_health',
                    value_text=f"{category.name} -> {trend_status}",
                    value_numeric=avg_interest,
                    embedding_context=category.embedding # Guardamos el vector de la categoría
                )

                time.sleep(random.uniform(2, 5)) # Pause to be polite

            except Exception as e:
                logger.error(f"❌ Error analyzing category {category.name}: {e}")
                if "429" in str(e):
                    time.sleep(60)

    def diagnose_trend(self, series):
        """Calcula si la tendencia sube o baja."""
        if len(series) < 8: return "UNKNOWN"
        first_half = series.iloc[:4].mean()
        last_half = series.iloc[-4:].mean()
        
        if last_half > first_half * 1.3: return "RISING 📈"
        if last_half < first_half * 0.7: return "FALLING 📉"
        return "STABLE ➡️"

    def perform_mass_action(self, category, action):
        """
        Afecta a todos los clusters que pertenecen a esta categoría.
        Nota: Asumimos coincidencia por texto en 'concept_name' o FK real si existiera.
        """
        # Búsqueda laxa por ahora (concept_name contains Category Name)
        # En futuro: Usar vector similarity search aca también para encontrar productos
        
        clusters = UniqueProductCluster.objects.filter(representative_product__title__icontains=category.name)
        
        if not clusters.exists(): 
            return

        if action == "SLEEP":
            clusters.update(is_candidate=False, discard_reason="Category Cold")
        elif action == "WAKE_UP":
            # Solo despertamos si no fueron descartados por otras razones (ej: profit negativo)
            clusters.filter(is_discarded=False).update(seasonality_flag="Category Hot", is_candidate=True)
            
        logger.info(f"      Running action {action} on {clusters.count()} clusters.")
