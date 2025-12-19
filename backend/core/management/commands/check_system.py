import os
import sys
import pathlib
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from core.models import Product, UniqueProductCluster, ProductClusterMembership, Supplier, Warehouse, ProductEmbedding

class Command(BaseCommand):
    help = 'Performs a complete system check (Health Check, Integrity, Stats)'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- DAHELL INTELLIGENCE - SYSTEM HEALTH CHECK ---\n")
        
        # 1. Environment & Config
        self.check_env()

        # 2. Database Connection & Integrity
        self.check_database()

        # 3. File System (Raw Data)
        self.check_filesystem()

        # 4. Critical Dependencies
        self.check_dependencies()

        # 5. Business Stats
        self.check_business_stats()
        
        self.stdout.write("\n[OK] System Check Completed.\n")

    def check_env(self):
        self.stdout.write("1. ENVIRONMENT VARIABLES")
        required_vars = [
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST',
            'DROPI_EMAIL', 'DROPI_PASSWORD'
        ]
        
        all_ok = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                display_val = '********' if 'PASSWORD' in var else value
                self.stdout.write(f"  [OK] {var}: {display_val}")
            else:
                self.stdout.write(f"  [MISSING] {var}")
                all_ok = False
        
        if not all_ok:
            self.stdout.write("  [VARNING] Critical environment variables are missing!")

    def check_database(self):
        self.stdout.write("\n2. DATABASE CONNECTION")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(f"  [OK] Connected to PostgreSQL")
                
                # Check pgvector
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                if cursor.fetchone():
                    self.stdout.write("  [OK] Extension 'pgvector': Installed")
                else:
                    self.stdout.write(f"  [FAIL] Extension 'pgvector': NOT INSTALLED")

        except Exception as e:
            self.stdout.write(f"  [FAIL] Database Connection Failed: {e}")

    def check_filesystem(self):
        self.stdout.write("\n3. FILE SYSTEM (Raw Data)")
        raw_dir = pathlib.Path("raw_data")
        if raw_dir.exists():
            files = list(raw_dir.glob("*.jsonl"))
            total_size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
            self.stdout.write(f"  [OK] raw_data/ exists")
            self.stdout.write(f"  Found {len(files)} JSONL files ({total_size_mb:.2f} MB)")
        else:
            self.stdout.write(f"  [WARNING] raw_data/ directory NOT found.")

    def check_dependencies(self):
        self.stdout.write("\n4. CRITICAL PYTHON DEPENDENCIES")
        # Removed psutil from check as it is not strictly required for server run
        libs = ['psycopg2', 'numpy', 'pandas', 'selenium', 'torch', 'transformers', 'PIL', 'requests']
        for lib in libs:
            try:
                __import__(lib)
                self.stdout.write(f"  [OK] {lib}: Installed")
            except ImportError:
                if lib == 'PIL':
                    try:
                        import PIL
                        self.stdout.write(f"  [OK] {lib} (Pillow): Installed")
                        continue
                    except:
                        pass
                self.stdout.write(f"  [FAIL] {lib}: NOT INSTALLED")

    def check_business_stats(self):
        self.stdout.write("\n5. BUSINESS INTELLIGENCE STATS")
        try:
            # Products
            total_products = Product.objects.count()
            self.stdout.write(f"  Products: {total_products}")

            # Vectors
            valid_vectors = ProductEmbedding.objects.filter(embedding_visual__isnull=False).count()
            self.stdout.write(f"  Vectors (Visual): {valid_vectors}")

            # Clusters
            total_clusters = UniqueProductCluster.objects.count()
            self.stdout.write(f"  Clusters: {total_clusters}")

        except Exception as e:
            self.stdout.write(f"  [FAIL] Error fetching stats: {e}")
