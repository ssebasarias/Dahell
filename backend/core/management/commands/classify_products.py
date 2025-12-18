from django.core.management.base import BaseCommand
from core.models import Product
from core.ai_classifier import classify_term
import logging
import time

# Setup Logging
logger = logging.getLogger("taxonomy_agent")
logger.setLevel(logging.INFO)

class Command(BaseCommand):
    help = 'Agent 1: Taxonomy Classifier (The Labeler). Assigns Concepts to Products.'

    def handle(self, *args, **options):
        # Prevent double logging
        if len(logger.handlers) == 0:
            console = logging.StreamHandler()
            logger.addHandler(console)
            
        logger.info("🏷️ AGENT 1: TAXONOMY CLASSIFIER STARTED")
        
        while True:
            # 1. Fetch unclassified products
            # We filter for products that don't have a concept yet
            pending_products = Product.objects.filter(
                taxonomy_concept__isnull=True,
                is_active=True
            ).order_by('-created_at')[:50]
            
            if not pending_products.exists():
                logger.info("💤 No pending products to classify. Sleeping 30s...")
                time.sleep(30)
                continue
            
            logger.info(f"⚡ Processing batch of {pending_products.count()} products...")
            
            for prod in pending_products:
                try:
                    self.classify_product(prod)
                    # Rate limit to avoid overloading the local LLM
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"❌ Error classifying product {prod.product_id}: {e}")
            
            # Sleep between batches
            time.sleep(2)

    def classify_product(self, prod):
        # COMBINED CONTEXT: Title + Intro of Description
        term = prod.title or ""
        desc = prod.description or ""
        
        # Le damos un poco mas de contexto al AI (Primero 100 chars del titulo + 150 de desc)
        # Limpiamos HTML basico si hubiera (Dropi a veces manda HTML)
        import re
        clean_desc = re.sub(r'<[^>]+>', ' ', desc)[:200]
        
        full_context = f"{term} | {clean_desc}".strip()[:300]
        
        # logger.info(f"   🤔 Thinking about: '{full_context[:50]}...'")
        
        result = classify_term(full_context)
        
        if result:
            # Extract fields
            concept_name = result.get('concept_name')
            industry = result.get('parent_industry')
            level = result.get('classification')
            
            if concept_name:
                prod.taxonomy_concept = concept_name
                prod.taxonomy_industry = industry
                prod.taxonomy_level = level
                # UPDATE SPECIFIC FIELDS ONLY to avoid touching generated columns like profit_margin
                prod.save(update_fields=['taxonomy_concept', 'taxonomy_industry', 'taxonomy_level'])
                logger.info(f"   ✅ {term[:30]}... -> [{concept_name}] ({level})")
            else:
                logger.warning(f"   ⚠️ No concept name returned for {term}")
                # Mark as processed to avoid infinite loop
                prod.taxonomy_concept = "UNKNOWN"
                prod.save(update_fields=['taxonomy_concept'])
