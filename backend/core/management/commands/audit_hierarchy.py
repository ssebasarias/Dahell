
from django.core.management.base import BaseCommand
from core.models import Product, UniqueProductCluster, Category
from django.db import connection

class Command(BaseCommand):
    help = 'Audits the 3-Level Hierarchy State'

    def handle(self, *args, **options):
        self.stdout.write("🔍 AUDITORÍA DE JERARQUÍA (3 NIVELES)\n")

        # Nivel 1: Industrias (Categorías Padre)
        industries = Product.objects.values_list('taxonomy_industry', flat=True).distinct()
        valid_industries = [i for i in industries if i]
        self.stdout.write(f"1️⃣ NIVEL 1 (Industrias Detectadas en Productos): {len(valid_industries)}")
        for ind in valid_industries[:10]:
             self.stdout.write(f"   - {ind}")

        # Nivel 2: Conceptos
        concepts = Product.objects.values_list('taxonomy_concept', flat=True).distinct()
        valid_concepts = [c for c in concepts if c]
        self.stdout.write(f"\n2️⃣ NIVEL 2 (Conceptos Generados): {len(valid_concepts)}")
        for con in valid_concepts[:10]:
             self.stdout.write(f"   - {con}")

        # Nivel 3: Clusters de Producto
        clusters = UniqueProductCluster.objects.count()
        self.stdout.write(f"\n3️⃣ NIVEL 3 (Clusters de Producto Únicos): {clusters}")
        
        # Validar Coherencia: ¿Cuántos productos tienen la cadena completa?
        full_chain = Product.objects.filter(
            taxonomy_industry__isnull=False,
            taxonomy_concept__isnull=False
        ).exclude(taxonomy_industry='', taxonomy_concept='').count()
        
        total = Product.objects.count()
        
        self.stdout.write(f"\n📊 COBERTURA:")
        self.stdout.write(f"   - Total Productos: {total}")
        self.stdout.write(f"   - Con Jerarquía Parcial (Ind/Conc): {full_chain} ({(full_chain/total*100) if total else 0:.1f}%)")

        # Muestra de Jerarquía Real
        self.stdout.write(f"\n✨ EJEMPLO REAL DE JERARQUÍA (Top 5):")
        sample = Product.objects.filter(taxonomy_industry__isnull=False)[:5]
        for p in sample:
            cluster_id = "N/A"
            if hasattr(p, 'cluster_membership'):
                cluster_id = p.cluster_membership.cluster_id
            self.stdout.write(f"   [{p.taxonomy_industry}] -> [{p.taxonomy_concept}] -> [{p.title[:30]}...] (Cluster: {cluster_id})")

