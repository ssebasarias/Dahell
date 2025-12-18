import logging
import datetime
from django.core.management.base import BaseCommand
from django.db.models import F
from core.models import FutureEvent, Category, UniqueProductCluster, MarketIntelligenceLog

try:
    from pgvector.django import L2Distance, CosineDistance
except ImportError:
    L2Distance = None

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Phase 2.5 (V3): The Prophet. Predicts events using Vector DB and activates related Categories.'

    def handle(self, *args, **options):
        logger.info("🔮 Invoking The Prophet (Vector Edition)...")
        
        if not L2Distance:
            logger.error("❌ PGVector not installed in Django environment. Cannot perform vector logic.")
            return

        today = datetime.date.today()
        logger.info(f"📅 Today is: {today.strftime('%Y-%m-%d')}")

        # 1. Buscar Eventos Activos o Entrantes en DB
        # Lógica: Eventos donde (FechaInicio - PrepDays) <= Hoy <= FechaFin
        # Como Django ORM con fechas calculadas es complejo, iteramos los activos (son pocos, <50)
        events = FutureEvent.objects.filter(is_active=True)
        
        active_events = []
        
        for event in events:
            # Normalizar año del evento al año actual para comparar
            try:
                evt_start = event.date_start.replace(year=today.year)
            except ValueError:
                continue # 29 feb error

            # Manejo de año nuevo (si estamos en Dic y el evento es Ene)
            if today.month == 12 and evt_start.month == 1:
                evt_start = evt_start.replace(year=today.year + 1)
            
            prep_start = evt_start - datetime.timedelta(days=event.prep_days)
            
            days_until_start = (evt_start - today).days
            days_until_prep = (prep_start - today).days
            
            # Si estamos dentro de la ventana de preparación o el evento está activo
            if days_until_prep <= 0 and days_until_start > -15: # -15 para mantenerlo activo un poco post-inicio
                status = "ACTIVE" if days_until_start <= 0 else "PREPARING"
                
                logger.info(f"🔔 Event Detected: {event.name} ({status}) - Days to Start: {days_until_start}")
                
                self.activate_categories_for_event(event, status, days_until_start)
                active_events.append(event)

        if not active_events:
            logger.info("💤 No commercial events on the immediate radar.")

    def activate_categories_for_event(self, event, status, days_to_start):
        """
        Usa Vectores para encontrar qué categorías vender.
        """
        if event.embedding is None:
            logger.warning(f"   ⚠️ Event {event.name} has no vector. Skipping semantic match.")
            return

        # 2. Búsqueda Vectorial: Encuentra Categorías Semánticamente Similares al Evento
        # "Navidad" debería matchear con "Juguetes", "Decoración", "Luces"
        # Usamos L2Distance o CosineDistance (Cosine es mejor para MiniLM)
        
        # Umbral de similitud (ajustable)
        # Cosine Distance: 0 (identico) a 2 (opuesto). < 0.6 es decente para MiniLM
        related_cats = Category.objects.annotate(
            distance=CosineDistance('embedding', event.embedding)
        ).order_by('distance').filter(distance__lt=0.6)[:5] # Top 5 categorías

        if not related_cats.exists():
            logger.info(f"   🤷 No matching categories found for {event.name} in DB.")
            return

        logger.info(f"   🎯 Target Categories for {event.name}:")
        
        for cat in related_cats:
            similarity = 1 - cat.distance # Convertir distancia a similitud
            logger.info(f"      - {cat.name} (Match: {similarity:.2f})")
            
            # 3. Activar Productos de esta Categoría
            # Aquí es donde 'resucitamos' productos dormidos
            self.awaken_products(cat, event.name)

            # 4. Log de Inteligencia
            MarketIntelligenceLog.objects.create(
                cluster=None,
                source='the_prophet',
                data_point='event_category_match',
                value_text=f"{event.name} -> {cat.name}",
                value_numeric=similarity,
                embedding_context=event.embedding # Guardamos el vector del evento como contexto
            )

    def awaken_products(self, category, event_name):
        """
        Busca clusters de esta categoría y los marca como Oportunidad de Temporada.
        """
        # Nota: Asumiendo relación ProductCategory -> Product -> Cluster
        # Esto requiere joins complejos, simplificamos buscando por nombre de categoría en 'concept_name' si existiera
        # O idealmente, UniqueProductCluster debería tener FK a Category. 
        # Por ahora, usamos búsqueda texto laxa en concept_name/title como fallback
        
        count = UniqueProductCluster.objects.filter(
            is_candidate=False, # Solo despertar los que no son candidatos ya
            representative_product__title__icontains=category.name # Fallback simple
        ).update(
            is_candidate=True,
            seasonality_flag=f"SEASON: {event_name}",
            trend_score=80 # Score alto artificial por temporada
        )
        
        if count > 0:
            logger.info(f"      ✨ Woke up {count} products for {category.name}")
