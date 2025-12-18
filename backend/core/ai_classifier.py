import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
# Intento de compatibilidad Pydantic V1/V2
try:
    from langchain_core.pydantic_v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
from typing import Literal

# Log Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. Definir Estructura de Salida (JSON Estricto) ---
class TaxonomyClassification(BaseModel):
    term: str = Field(description="El término analizado")
    classification: Literal["INDUSTRY", "CONCEPT", "PRODUCT", "UNKNOWN"] = Field(
        description="Nivel taxonómico: INDUSTRY (Sector amplio), CONCEPT (Tipo de producto genérico), PRODUCT (Item específico/marca)."
    )
    parent_industry: str = Field(description="La industria madre sugerida (ej: 'Tecnología', 'Moda').")
    reason: str = Field(description="Breve explicación de por qué se clasificó así.")

# --- 2. El Taxónomo ---
class TaxonomistAI:
    def __init__(self, model_name="llama3.1"):
        # URL de host.docker.internal para conectar desde Docker al Windows Host
        # Si corre local fuera de docker, usar localhost.
        self.llm = ChatOllama(
            model=model_name,
            base_url="http://host.docker.internal:11434", 
            temperature=0, # Temperatura 0 para máxima precisión y determinismo
            format="json" # Forzar modo JSON nativo de Ollama
        )
        
        # Estructura del Prompt con Few-Shot Learning (Ejemplos)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto Taxónomo de E-commerce Senior. Tu trabajo es clasificar términos de búsqueda en 3 niveles jerárquicos.

            NIVELES:
            1. INDUSTRY (Industria/Categoría Padre): Términos muy amplios que agrupan miles de productos. No se compran directamente. 
               Ejemplos: "Tecnología", "Hogar", "Deportes", "Belleza", "Ropa Mujer".

            2. CONCEPT (Concepto/Nicho): Grupos de productos específicos que satisfacen una necesidad concreta. Son "comprables" pero genéricos.
               Ejemplos: "Audífonos Inalámbricos", "Silla Ergonómica", "Labial Mate", "Botas de Lluvia", "Aspiradora Robot".
               *ESTE ES EL NIVEL MÁS IMPORTANTE.*

            3. PRODUCT (Producto Específico): Items con marca, modelo o especificaciones únicas.
               Ejemplos: "iPhone 15 Pro", "Nike Air Force 1", "Crema Nivea Q10", "Taladro DeWalt 20V".

            Responde SIEMPRE en formato JSON válido que cumpla con este esquema:
            {{
                "term": "termino original",
                "classification": "NIVEL",
                "concept_name": "Nombre Estandarizado del Concepto (Singular, Capitalized)",
                "parent_industry": "Industria Madre",
                "reason": "explicación"
            }}
            
            Ejemplos:
            Input: "Lenovo LP40 Pro"
            Output: {{ "classification": "PRODUCT", "concept_name": "Audífonos Inalámbricos", "parent_industry": "Tecnología", ... }}
            
            Input: "Silla Gamer Ergonómica"
            Output: {{ "classification": "CONCEPT", "concept_name": "Silla Gamer", "parent_industry": "Muebles", ... }}
            """),
            ("user", "Clasifica el término: '{input}'")
        ])

        # Chain: Prompt -> LLM -> JSON Parser (implícito en el prompt o via structured_output)
        # Llama 3 suele ser muy bueno respondiendo JSON si se le pide format="json" en el constructor.
        self.chain = self.prompt | self.llm

    def classify(self, term):
        """
        Clasifica un término usando Llama 3.
        Retorna dict: {'classification': '...', 'reason': ...}
        """
        try:
            # Invocar al modelo
            response = self.chain.invoke({"input": term})
            
            # Parsear contenido (Ollama devuelve string en .content)
            import json
            # A veces el modelo pone texto antes del json, intentamos limpiar
            content = response.content.strip()
            
            # Buscar el primer '{' y último '}'
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data
            else:
                logger.error(f"❌ Failed to parse JSON from AI: {content}")
                return None

        except Exception as e:
            logger.error(f"❌ AI Classification Error: {e}")
            return None

# Singleton Helper
_taxonomist = None
def classify_term(term):
    global _taxonomist
    if _taxonomist is None:
        _taxonomist = TaxonomistAI()
    return _taxonomist.classify(term)
