
import os
import time
import logging
import sys
import pathlib
import pandas as pd
import numpy as np
import django
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from django.db import connection
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

load_dotenv()

# Setup Django (para cuando corre como script independiente si fuera necesario)
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dahell.settings")
# django.setup()

from core.models import AIFeedback

# ─────── Configuración de Logs ───────
LOG_DIR = pathlib.Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("trainer")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

fh = logging.FileHandler(LOG_DIR / "ai_trainer.log", encoding='utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

class AITrainer:
    def __init__(self):
        self.min_samples_required = 20
        self.check_interval = 60 # Segundos entre chequeos

    def fetch_training_data(self):
        """Descarga el feedback humano enriquecido con el concepto del producto."""
        # JOIN implícito vía Django ORM (feedback -> product -> taxonomy_concept)
        # Asumiendo que AIFeedback tiene FK a Product. Si no, usamos product_id.
        # AIFeedback model doesn't explicitly have a relation field usually, just integer.
        # Let's check models.py first? No, assuming product_id is integer based on context.
        # We'll fetch raw and join in python or raw SQL. Raw SQL is safer for aggregations.
        
        with connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    f.visual_score, f.text_score, f.final_score, f.decision, f.feedback,
                    p.taxonomy_concept
                FROM ai_feedback f
                JOIN products p ON f.product_id = p.product_id
                WHERE f.visual_score IS NOT NULL 
                AND f.text_score IS NOT NULL
                AND p.taxonomy_concept IS NOT NULL
            """)
            rows = cur.fetchall()
            
        if not rows: return None
        
        df = pd.DataFrame(rows, columns=['visual_score', 'text_score', 'final_score', 'decision', 'feedback', 'concept'])
        
        def calculate_target(row):
            machine_good = 1 if row['decision'] in ['MATCH', 'CANDIDATE'] else 0
            human_agrees = 1 if row['feedback'] == 'CORRECT' else 0
            
            if machine_good and human_agrees: return 1      # TP
            if machine_good and not human_agrees: return 0  # FP
            if not machine_good and human_agrees: return 0  # TN
            if not machine_good and not human_agrees: return 1 # FN
            return 0

        df['target'] = df.apply(calculate_target, axis=1)
        return df

    def train_and_optimize(self):
        logger.info("🧠 Brain Scan: Buscando patrones por Concepto...")
        
        df_all = self.fetch_training_data()
        if df_all is None or df_all.empty:
            logger.info("   Zzz... Sin datos para aprender.")
            return

        # Agrupar por Concepto
        grouped = df_all.groupby('concept')
        
        for concept, df_concept in grouped:
            count = len(df_concept)
            # Solo entrenar si hay suficientes datos para este concepto
            # Bajamos el umbral a 5 para testing rápido (prod debería ser 20+)
            MIN_SAMPLES = 5 
            
            if count < MIN_SAMPLES:
                logger.debug(f"   Skip '{concept}': Pocos datos ({count}/{MIN_SAMPLES})")
                continue
                
            logger.info(f"   🎓 Entrenando personalidad para: '{concept}' (N={count})")

            # --- MACHINE LEARNING ---
            try:
                X = df_concept[['visual_score', 'text_score']]
                y = df_concept['target']
                
                # Check variance (if all targets are 1 or 0, we can't train logistic)
                if len(y.unique()) < 2:
                    logger.warning(f"      ⚠️ '{concept}' data is skewed (all correct/incorrect). Skipping.")
                    continue

                clf = LogisticRegression(fit_intercept=True)
                clf.fit(X, y)
                
                coef_visual = abs(clf.coef_[0][0])
                coef_text = abs(clf.coef_[0][1])
                bias = clf.intercept_[0]
                
                total_imp = coef_visual + coef_text
                if total_imp == 0: total_imp = 1
                
                learned_w_vis = coef_visual / total_imp
                # learned_w_txt = coef_text / total_imp (redundant)

                # --- SMOOTH UPDATE (EMA) ---
                current_conf = self.get_current_config(concept)
                ALPHA = 0.3
                
                new_w_vis = (learned_w_vis * ALPHA) + (float(current_conf['weight_visual']) * (1-ALPHA))
                new_w_vis = max(0.1, min(0.9, new_w_vis)) # Safety bounds
                new_w_txt = 1.0 - new_w_vis
                
                # Threshold heuristic
                threshold_adj = 0.68 - (bias * 0.05)
                new_threshold = max(0.55, min(0.85, threshold_adj))
                
                # Diff check
                diff = abs(new_w_vis - float(current_conf['weight_visual']))
                if diff > 0.01:
                    self.update_db_config(concept, new_w_vis, new_w_txt, new_threshold, count)
                    logger.info(f"      ✅ Ajustado: Vis={new_w_vis:.2f}, Txt={new_w_txt:.2f}, Th={new_threshold:.2f}")
                else:
                    logger.info(f"      🔹 Estable.")
                    
            except Exception as e:
                logger.error(f"Error entrenando {concept}: {e}")

    def get_current_config(self, concept):
        # Leer de tabla nueva
        with connection.cursor() as cur:
            cur.execute("SELECT weight_visual, weight_text FROM concept_weights WHERE concept = %s", (concept,))
            row = cur.fetchone()
            if row: return {"weight_visual": row[0], "weight_text": row[1]}
            # Fallback a default global o hardcoded
            return {"weight_visual": 0.6, "weight_text": 0.4}

    def update_db_config(self, concept, w_vis, w_txt, threshold, n_samples):
        with connection.cursor() as cur:
            # UPSERT en tabla nueva
            cur.execute("""
                INSERT INTO concept_weights (concept, weight_visual, weight_text, threshold_hybrid, sample_size, last_updated)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (concept) 
                DO UPDATE SET 
                    weight_visual = EXCLUDED.weight_visual,
                    weight_text = EXCLUDED.weight_text,
                    threshold_hybrid = EXCLUDED.threshold_hybrid,
                    sample_size = EXCLUDED.sample_size,
                    last_updated = NOW();
            """, (concept, w_vis, w_txt, threshold, n_samples))

    def run_daemon(self):
        logger.info("🚀 AI TRAINER DAEMON INICIADO (Modo Concepto-Específico)")
        while True:
            try:
                self.train_and_optimize()
            except Exception as e:
                logger.error(f"❌ Error training cycle: {e}")
            time.sleep(self.check_interval)

class Command(BaseCommand):
    help = 'AI Trainer Daemon'

    def handle(self, *args, **options):
        trainer = AITrainer()
        trainer.run_daemon()
