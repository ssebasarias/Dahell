from django.core.management.base import BaseCommand
from core.models import UniqueProductCluster, MarketIntelligenceLog
from core.ai_classifier import classify_term
import requests
import logging
import time
import json
from datetime import datetime

# Setup Logging
logger = logging.getLogger("opportunity_validator")
logger.setLevel(logging.INFO)

class Command(BaseCommand):
    help = 'Phase 4: Validate Market Opportunity (Sensor Mode)'

    def handle(self, *args, **options):
        logger.info("🕵️ Starting Opportunity Validation Protocol...")
        
        # 1. Fetch Candidates (Clusters not yet validated or classified)
        candidates = UniqueProductCluster.objects.filter(
            taxonomy_type='UNKNOWN',
            is_discarded=False
        ).order_by('-total_competitors')[:50]  # Process in batches
        
        if not candidates.exists():
            logger.info("✅ No pending clusters to validate.")
            return

        logger.info(f"⚡ Processing {candidates.count()} candidate clusters...")

        for cluster in candidates:
            try:
                self.process_cluster(cluster)
            except Exception as e:
                logger.error(f"❌ Error processing cluster {cluster.cluster_id}: {e}")
                
            # Rate limiting for sensors
            time.sleep(1.5) 

    def process_cluster(self, cluster):
        # A. Define Search Term (Concept Name preferred, or Product Title)
        term = cluster.concept_name
        if not term or len(term) < 3:
            if cluster.representative_product:
                term = cluster.representative_product.title[:100] # Truncate for safety
            else:
                cluster.taxonomy_type = 'NO_DATA'
                cluster.save()
                return

        logger.info(f"\n🔍 Analyzing Cluster #{cluster.cluster_id}: '{term}'")

        # B. Taxonomy Classification (AI)
        logger.info("   🧠 Classifying Taxonomy...")
        taxonomy_result = classify_term(term)
        
        if not taxonomy_result:
            logger.warning("   ⚠️ AI Classification failed.")
            return

        cl_type = taxonomy_result.get('classification', 'UNKNOWN')
        cluster.taxonomy_type = cl_type
        cluster.save()
        
        logger.info(f"   🏷️ Type: {cl_type} | Reason: {taxonomy_result.get('reason')}")

        # Strategy Switch
        if cl_type == 'INDUSTRY':
            # Ignore industries for opportunity scoring (too broad)
            cluster.validation_log = "Skipped: Industry too broad."
            cluster.market_opportunity_score = 0
            cluster.save()
            return
        
        # C. The "Sensor" (MercadoLibre Questions)
        # Only for CONCEPTS or PRODUCTS
        questions = self.fetch_questions(term)
        q_vol = len(questions)
        logger.info(f"   📡 Sensor detected {q_vol} recent questions.")

        if q_vol == 0:
            cluster.validation_log = "No external demand signals (Silence)."
            cluster.save() 
            # We don't discard, just low score
        
        # D. Calculate Score (Heuristic)
        # Factors
        c_size = cluster.total_competitors # Internal Supply
        # Normalize Questions: 0-20 scale (20 questions is A LOT for a specific item)
        q_score = min(q_vol, 20) / 20.0 
        
        # Normalize Cluster Size: 1-10 scale
        c_score = min(c_size, 10) / 10.0
        
        # LLM Confidence (Fixed for now if classified)
        llm_score = 1.0 if cl_type in ['PRODUCT', 'CONCEPT'] else 0.5
        
        # Saturation Penalty (If too many people selling it, opportunity drops)
        # But for now, let's say max saturation (50 sellers) = 1.0 penalty
        sat_penalty = min(c_size, 50) / 50.0

        # Formula:
        # Opportunity = (Demand * 0.5) + (ProvenSupply * 0.2) + (AI_Conf * 0.2) - (Saturation * 0.1)
        # Adjusted User Formula: 
        # (cluster_size * 0.3) + (questions * 0.4) ...
        
        # Let's align with user's weights roughly but using normalized values
        final_score = (
            (c_score * 30.0) +      # Max 30 pts (Supply exists)
            (q_score * 40.0) +      # Max 40 pts (People want it)
            (llm_score * 20.0) -    # Max 20 pts (It's a valid item)
            (sat_penalty * 10.0)    # Minus up to 10 pts (Saturation)
        )
        
        # Cap at 100, flloor at 0
        final_score = max(0.0, min(100.0, final_score))
        
        logger.info(f"   📈 Score: {final_score:.1f}/100 (Q_Vol={q_vol}, Sellers={c_size})")

        # E. Save
        cluster.market_opportunity_score = final_score
        cluster.validation_log = f"Questions: {q_vol}. Examples: {questions[:2]}"
        cluster.save()

        # F. Log Insight
        if q_vol > 0:
            MarketIntelligenceLog.objects.create(
                cluster=cluster,
                source='mercadolibre_questions',
                data_point='external_interest',
                value_numeric=q_vol,
                value_text=json.dumps(questions[:5], ensure_ascii=False)
            )

    def fetch_questions(self, query):
        """Sensor: MercadoLibre Questions"""
        try:
            # 1. Search Item
            url = f"https://api.mercadolibre.com/sites/MCO/search?q={query}&limit=3"
            r = requests.get(url)
            if r.status_code != 200: return []
            
            items = r.json().get('results', [])
            all_questions = []
            
            for item in items:
                item_id = item['id']
                # 2. Get Questions
                q_url = f"https://api.mercadolibre.com/questions/search?item_id={item_id}&limit=5"
                qr = requests.get(q_url)
                if qr.status_code == 200:
                    qs = qr.json().get('questions', [])
                    for q in qs:
                        if 'text' in q:
                            all_questions.append(q['text'])
            
            return all_questions
        except Exception:
            return []
