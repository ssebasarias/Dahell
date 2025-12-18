import re
import logging
import datetime
from django.core.management.base import BaseCommand
from core.models import FutureEvent, Category
from core.ai_utils import encode_text

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Phase 0 (System): Parses the MD Calendar, cleans noise (emojis/md), vectorizes events, and seeds the DB.'

    def handle(self, *args, **options):
        logger.info("🌱 Starting Vector Seeding Process...")
        
        # 1. Procesar Calendario Comercial (MD)
        self.seed_events_from_md()
        
        # 2. Vectorizar Categorías Existentes (Si hay)
        self.vectorize_categories()

        logger.info("✅ Seeding Complete.")

    def seed_events_from_md(self, md_path='docs/CALENDARIO_COMERCIAL_CO.md'):
        """
        Lee el archivo MD, extrae las tablas, limpia emojis/markdown y guarda en DB.
        """
        logger.info(f"📖 Reading Calendar from {md_path}...")
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.error("❌ Calendar file not found!")
            return

        # Regex para parsear filas de tabla Markdown
        # Formato esperado: | Evento | Fecha | Ventana | Keywords | Notas |
        table_row_pattern = re.compile(r'\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|')

        count = 0
        for line in lines:
            if "---" in line or "| Evento" in line: # Headers o separadores
                continue
            
            match = table_row_pattern.search(line)
            if match:
                raw_name, raw_date, raw_prep, raw_keywords, raw_notes = match.groups()
                
                # A. LIMPIEZA DE RUIDO (Emojis, *, [])
                clean_name = self.clean_text(raw_name)
                clean_keywords = self.clean_text(raw_keywords)
                clean_notes = self.clean_text(raw_notes)
                
                # B. Parsing de Fecha (Aproximado para demo, idealmente más robusto)
                # Asumimos año actual por defecto
                start_date, end_date = self.parse_dates(raw_date)
                
                # C. Parsing de Prep Days
                prep_days = 30 # Default
                prep_match = re.search(r'(\d+)', raw_prep)
                if prep_match:
                    prep_days = int(prep_match.group(1))

                # D. Vectorización (El Cerebro)
                # Concatenamos Name + Keywords + Notes para un vector rico en contexto semántico
                semantic_text = f"{clean_name} {clean_keywords} {clean_notes}"
                vector = encode_text(semantic_text)

                # E. Guardar en DB
                event, created = FutureEvent.objects.update_or_create(
                    name=clean_name,
                    defaults={
                        'date_start': start_date,
                        'date_end': end_date,
                        'prep_days': prep_days,
                        'keywords': clean_keywords,
                        'embedding': vector, # PGVector guarda esto
                        'is_active': True
                    }
                )
                action = "Created" if created else "Updated"
                logger.info(f"   🗓️ {action} Event: {clean_name} (Prep: {prep_days}d)")
                count += 1
        
        logger.info(f"   ✨ Processed {count} events from Markdown.")

    def vectorize_categories(self):
        """
        Busca categorías sin vector y las vectoriza.
        """
        logger.info("📦 Checking Categories...")
        cats = Category.objects.all()
        updated = 0
        
        for cat in cats:
            # Si no tiene vector O queremos forzar actualización (podríamos agregar flag force)
            if cat.embedding is None:
                # Contexto rico: Nombre + Descripción (si existe)
                text_to_embed = f"{cat.name} {cat.description or ''}"
                clean = self.clean_text(text_to_embed)
                
                cat.embedding = encode_text(clean)
                cat.save()
                updated += 1
                logger.info(f"   🧬 Vectorized Category: {cat.name}")
        
        if updated > 0:
            logger.info(f"   ✅ Vectorized {updated} categories.")
        else:
            logger.info("   👍 All categories already vectorized.")

    def clean_text(self, text):
        """
        Elimina emojis, caracteres especiales de MD (*, _, `) y espacios extra.
        """
        if not text: return ""
        
        # 1. Quitar Emojis (Rango Unicode básico)
        # Esta regex cubre la mayoría de emojis comunes
        text = re.sub(r'[^\w\s,.-]', '', text) 
        
        # 2. Quitar Markdown (*negrita*, _cursiva_)
        text = text.replace('*', '').replace('_', '').replace('`', '')
        
        # 3. Normalizar espacios
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def parse_dates(self, date_str):
        """
        Intenta convertir strings como 'Enero 15' a objetos Date reales del año actual.
        """
        today = datetime.date.today()
        year = today.year
        
        # Mapeo meses español
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }
        
        clean_str = self.clean_text(date_str).lower()
        
        # Buscar "Mes Dia" (ej: Enero 15)
        # Regex simple: (palabra) (numero)
        match = re.search(r'([a-z]+)\s+(\d+)', clean_str)
        
        if match:
            month_name, day = match.groups()
            month_num = months.get(month_name[:3]) # Intentar matchear primeras 3 letras
            
            if month_num:
                try:
                    start_date = datetime.date(year, month_num, int(day))
                    # Si dice "Enero 15 - Feb 10", la logica de fin es mas compleja. 
                    # Por simplicidad ahora, start=end si no hay rango claro.
                    return start_date, start_date 
                except ValueError:
                    pass
        
        # Fallback si falla el parseo (Retornar hoy para no romper, o None)
        # Para evitar romper la DB, retornamos Enero 1 del año actual si falla
        return datetime.date(year, 1, 1), datetime.date(year, 1, 1)
