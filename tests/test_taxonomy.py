from django.core.management.base import BaseCommand
from core.ai_classifier import classify_term
import logging

logging.basicConfig(level=logging.INFO)

class Command(BaseCommand):
    help = 'Test Taxonomy Classifier'

    def handle(self, *args, **options):
        terms = ["Belleza", "Labial Mate larga duracion", "Samsung Galaxy S24 Ultra", "Muebles de Oficina", "Silla Gamer Ergonómica"]
        
        print("\n🧠 TESTING TAXONOMIST AI (Llama 3.1)...")
        print("-" * 60)
        
        for term in terms:
            print(f"🤔 Thinking about: '{term}'...")
            result = classify_term(term)
            
            if result:
                print(f"   🎯 Result: {result['classification']}")
                print(f"      Parent: {result['parent_industry']}")
                print(f"      Reason: {result['reason']}")
            else:
                print("   ❌ Failed to classify.")
            print("-" * 60)
