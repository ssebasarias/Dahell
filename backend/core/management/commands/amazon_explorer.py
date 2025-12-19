
import os
import time
import requests
import logging
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from core.models import UniqueProductCluster
from dotenv import load_dotenv
import random

load_dotenv()

# Setup Logging
logger = logging.getLogger("amazon_explorer")
logger.setLevel(logging.INFO)
# (Add Handler if missing)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s [AMAZON] %(message)s'))
    logger.addHandler(ch)

class Command(BaseCommand):
    help = 'Amazon Explorer: Scrapes demand data using a "No-API" approach (Requests + User-Agent Rotation).'

    def add_arguments(self, parser):
        parser.add_argument('--force-all', action='store_true', help='Scan all candidate clusters regardless of state')

    def handle(self, *args, **options):
        logger.info("📦 AMAZON EXPLORER STARTED")
        
        while True:
            # 1. Select High-Potential Clusters
            # Logic: We want things that passed Dropi Tier (LOW/MID) AND performed okay in MercadoLibre (OPPORTUNITY/HIGH)
            # OR just general candidates.
            # For now, let's grab anything that needs US Market validation.

            candidates = UniqueProductCluster.objects.filter(
                dropi_competition_tier__in=['LOW', 'MID'],
                # Example: market_opportunity_score > 0 means it passed basic MELI check
                # You can adjust this filter.
            ).exclude(
                market_saturation_level='AMAZON_CHECKED' # Flag to avoid loops
            ).order_by('-market_opportunity_score')[:5]

            if not candidates.exists():
                logger.info("💤 No amazon-ready candidates. Sleeping 120s...")
                time.sleep(120)
                continue

            for cluster in candidates:
                self.analyze_amazon(cluster)
                # Respect Amazon's anti-bot (Sleep randomized)
                sleep_time = random.uniform(5, 15)
                time.sleep(sleep_time)
            
            time.sleep(10)

    def analyze_amazon(self, cluster):
        concept = cluster.concept_name
        if not concept: return

        logger.info(f"🔎 Analyzing Amazon for: '{concept}'")
        
        # 1. Search Request (Headers are crucial)
        # Using a specialized User-Agent to look like a desktop browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.amazon.com/'
        }
        
        # Search URL (Amazon US)
        search_query = concept.replace(' ', '+')
        url = f"https://www.amazon.com/s?k={search_query}"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"   Blocked by Amazon? Status: {resp.status_code}")
                return
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # 2. Extract Data (Sales & Reviews)
            results = soup.select('div.s-result-item[data-component-type="s-search-result"]')
            
            total_sales_signal = 0
            review_counts = []
            valid_items = 0
            
            for item in results[:10]: # Check top 10 organic
                # Extract Title
                title_el = item.select_one('h2 a span')
                if not title_el: continue
                title = title_el.text.strip()
                
                # Extract "X bought in past month" (The Golden Metric)
                # Amazon CSS classes change, but text usually contains "bought in past month"
                sales_text = ""
                # Try finding the span that contains that specific text
                sales_span = item.find(lambda tag: tag.name == "span" and "bought in past month" in tag.text)
                if sales_span:
                    sales_text = sales_span.text
                    # Parse "500+ bought..." -> 500
                    try:
                        num_str = sales_text.split('+')[0].replace('K', '000').strip()
                        if num_str.isdigit():
                            total_sales_signal += int(num_str)
                    except: pass
                
                # Extract Reviews
                # Usually in a span with aria-label containing "stars"
                # Or class "a-size-base s-underline-text"
                reviews_el = item.select_one('span.a-size-base.s-underline-text')
                if reviews_el:
                    try:
                        # "1,200" -> 1200
                        count = int(reviews_el.text.replace(',', ''))
                        review_counts.append(count)
                    except: pass
                
                valid_items += 1

            # 3. heuristic Analysis
            # If we see "bought in past month" labels, use them.
            # If not, use the Review * 10 multiplier (rule of thumb for monthly sales on established items)
            
            estimated_monthly_demand = 0
            if total_sales_signal > 0:
                estimated_monthly_demand = total_sales_signal
                method = "DIRECT_DATA (Amazon)"
            else:
                # Fallback: Sum of top 5 review counts * 0.5 (Conservative estimate of monthly velocity)
                # Very rough, but better than nothing.
                if review_counts:
                    avg_reviews = sum(review_counts) / len(review_counts)
                    estimated_monthly_demand = int(avg_reviews * 0.5) 
                    method = "REVIEW_INFERENCE"
                else:
                    estimated_monthly_demand = 0
                    method = "NONE"

            logger.info(f"   🇺🇸 Amazon US Signal: ~{estimated_monthly_demand} monthly sales ({method})")
            
            # Save to Cluster (using validation_log to avoid schema changes for now, or update market fields)
            # We can reuse 'search_volume_estimate' as a global demand proxy
            current_vol = cluster.search_volume_estimate or 0
            cluster.search_volume_estimate = current_vol + estimated_monthly_demand
            
            # Log the finding
            log_entry = f"[AMAZON] {estimated_monthly_demand} monthly demand. Method: {method}. Top result: {title[:30]}..."
            if cluster.validation_log:
                cluster.validation_log += "\n" + log_entry
            else:
                cluster.validation_log = log_entry

            # Mark processed
            cluster.market_saturation_level = 'AMAZON_CHECKED' 
            cluster.save()

        except Exception as e:
            logger.error(f"   Error analyzing Amazon: {e}")
