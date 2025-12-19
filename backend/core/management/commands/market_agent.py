
import os
import time
import requests
import numpy as np
import logging
fromPIL import Image
from io import BytesIO
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import UniqueProductCluster, ProductEmbedding
from transformers import CLIPProcessor, CLIPModel
import torch
from dotenv import load_dotenv

load_dotenv()

# Setup Logging
logger = logging.getLogger("market_agent")
logger.setLevel(logging.INFO)
# (Assuming logging config is handled by Django or global config, but adding basic handler)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# MercadoLibre API Config
MELI_SITE = os.getenv("MELI_SITE", "MCO") # MCO = Colombia
MELI_API_URL = f"https://api.mercadolibre.com/sites/{MELI_SITE}/search"

class Command(BaseCommand):
    help = 'Agent 3: Market Validator (MercadoLibre/External). Filters visually similar competitors.'

    def __init__(self):
        super().__init__()
        # Load AI Model (Reusing CLIP logic for visual filtering)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🧠 MarketAgent Loading CLIP ({self.device})...")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        logger.info("✅ CLIP Loaded.")

    def handle(self, *args, **options):
        logger.info("🕵️ MARKET AGENT STARTED")
        
        while True:
            # 1. Fetch Candidates (Clusters already classified LOW/MID competition in Dropi)
            # Logic: We only validate clusters that have low competition internally (meaning they passed the first funnel)
            # and haven't been fully analyzed externally (market_opportunity_score = 0 or analysis_level < 1)
            candidates = UniqueProductCluster.objects.filter(
                dropi_competition_tier__in=['LOW', 'MID'], 
                # Avoid re-scanning constantly. 
                # Ideally, we flag them as 'ANALYZED_EXTERNALLY' or use a timestamp.
                # For now, let's use market_opportunity_score == 0 as "pending"
                market_opportunity_score=0 
            ).order_by('-created_at')[:10]

            if not candidates.exists():
                logger.info("💤 No candidates to validate. Sleeping 60s...")
                time.sleep(60)
                continue

            for cluster in candidates:
                try:
                    self.validate_cluster(cluster)
                except Exception as e:
                    logger.error(f"❌ Error validating cluster {cluster.cluster_id}: {e}")
            
            time.sleep(5)

    def validate_cluster(self, cluster):
        concept = cluster.concept_name
        if not concept:
            logger.warning(f"⚠️ Cluster {cluster.cluster_id} has no concept name. Skipping.")
            return

        logger.info(f"🔍 Searching MercadoLibre for: '{concept}'")
        
        # 1. Search API
        params = {'q': concept, 'limit': 50}
        try:
            resp = requests.get(MELI_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"   API Error: {e}")
            return

        results = data.get('results', [])
        if not results:
            logger.info(f"   📉 Zero results found for '{concept}'. Possible Dead Market or Opportunity?")
            # TODO: Logic for zero results
            cluster.market_opportunity_score = -1 # Mark as checked but empty
            cluster.save()
            return

        # 2. Visual Filtering
        # We need the vector of our cluster's representative product
        rep_product = cluster.representative_product
        if not rep_product: return

        # Load embedding from DB
        try:
            rep_embedding_obj = ProductEmbedding.objects.get(product_id=rep_product.product_id)
            if not rep_embedding_obj.embedding_visual:
                logger.warning("   ⚠️ Representative product has no vector. Skipping visual check.")
                return
            target_vector = np.array(rep_embedding_obj.embedding_visual)
        except ProductEmbedding.DoesNotExist:
            return

        valid_competitors = []
        
        # Limit processing to avoid spamming downloads
        for item in results[:20]: 
            img_url = item.get('thumbnail', '').replace('-I.jpg', '-O.jpg') # Try to get high quality
            if not img_url: continue

            # Download & Vectorize
            try:
                img_vector = self.vectorize_image_from_url(img_url)
                if img_vector is None: continue
                
                # Cosine Similarity
                sim = np.dot(target_vector, img_vector)
                
                # Threshold: 0.85 (Strict enough to ignore cases/accessories, loose enough for different angles)
                if sim > 0.85:
                    valid_competitors.append(item)
                    # logger.info(f"     ✅ Match ({sim:.2f}): {item['title'][:30]}...")
                # else:
                    # logger.info(f"     ❌ No Match ({sim:.2f}): {item['title'][:30]}...")
            except Exception as e:
                pass

        # 3. Analyze Valid Comps
        count = len(valid_competitors)
        if count == 0:
            logger.info("   🧹 All results filtered out visually (No exact matches).")
            cluster.market_saturation_level = 'EMPTY'
            cluster.market_avg_price = 0
            cluster.save()
            return

        prices = [float(i['price']) for i in valid_competitors if i.get('price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Estimating Sales (Review * 50 rule + Sold Qty from API if reliable)
        # MELI API 'sold_quantity' is mostly '5, 25, 50, 100, 500, 5000' buckets.
        total_estimated_sales = 0
        for comp in valid_competitors:
            sold = comp.get('sold_quantity', 0)
            # Use sold directly or estimate? MELI sold_quantity is lifetime usually.
            # Newer rule: check "official_store_id" or "stop_time" to judge freshness? 
            # For now, simple sum of 'sold_quantity' from visible competitors gives Market Depth.
            total_estimated_sales += sold

        # Profit Calculation
        dropi_price = float(cluster.average_price or 0)
        margin = avg_price - dropi_price

        logger.info(f"   📊 Analysis Result: {count} competitors found.")
        logger.info(f"      Dropi Cost: ${dropi_price:,.0f} | Market Price: ${avg_price:,.0f}")
        logger.info(f"      Potential Margin: ${margin:,.0f}")
        logger.info(f"      Market Depth (Sold): {total_estimated_sales}")

        # Update Cluster
        cluster.market_avg_price = avg_price
        cluster.potential_margin = margin
        cluster.search_volume_estimate = total_estimated_sales # Storing depth here for now
        
        # Scoring (Simple Heuristic V1)
        # If Margin is positive and healthy (>30% of cost) AND Competition is not crazy
        if dropi_price > 0:
            roi = (margin / dropi_price) * 100
        else: 
            roi = 0
            
        cluster.market_opportunity_score = roi # Simple ROI score
        
        if count > 30:
            cluster.market_saturation_level = 'SATURATED'
        elif count > 10:
            cluster.market_saturation_level = 'HIGH'
        else:
            cluster.market_saturation_level = 'OPPORTUNITY'

        cluster.save()

    def vectorize_image_from_url(self, url):
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code != 200: return None
            image = Image.open(BytesIO(resp.content)).convert("RGB")
            
            inputs = self.processor(images=image, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                features = self.model.get_image_features(**inputs)
            
            # Normalize
            features = features / features.norm(p=2, dim=-1, keepdim=True)
            return features.cpu().numpy()[0]
        except:
            return None
