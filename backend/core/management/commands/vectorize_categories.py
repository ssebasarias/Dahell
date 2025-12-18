import logging
from django.core.management.base import BaseCommand
from core.models import Category
from core.ai_utils import encode_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Utility: Generate/Update embeddings for all Categories in DB.'

    def handle(self, *args, **options):
        logger.info("🧬 Starting Category Vectorization...")
        
        categories = Category.objects.all()
        count = 0
        updated = 0
        
        for cat in categories:
            # Construir texto semántico rico
            # Combina nombre + descripción (si existe) para mejor contexto
            semantic_text = f"{cat.name}"
            if cat.description:
                semantic_text += f" - {cat.description}"
            
            # Generar Vector (384 dim)
            vector = encode_text(semantic_text)
            
            # Guardar
            cat.embedding = vector
            cat.save()
            updated += 1
            
            if updated % 10 == 0:
                self.stdout.write(f"   ...processed {updated} categories")

        logger.info(f"✅ Success. Vectorized {updated} categories.")
