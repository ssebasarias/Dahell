"""
Script de Validación Automática: JSON Scraper vs Esquema DB
============================================================
Este script compara la estructura del JSON del scraper con el esquema
de la base de datos para detectar incompatibilidades automáticamente.
"""

import json
import psycopg2
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de conexión a la BD
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'dahell_db'),
    'user': os.getenv('POSTGRES_USER', 'dahell_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'secure_password_123'),
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': os.getenv('POSTGRES_PORT', '5433')
}

def get_db_schema() -> Dict[str, Dict]:
    """Obtiene el esquema completo de la base de datos"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        table_name, 
        column_name, 
        data_type, 
        character_maximum_length,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    schema = {}
    for table, column, dtype, max_len, nullable, default in rows:
        if table not in schema:
            schema[table] = {}
        schema[table][column] = {
            'type': dtype,
            'max_length': max_len,
            'nullable': nullable == 'YES',
            'default': default
        }
    
    conn.close()
    return schema

def validate_json_sample(json_file_path: str, schema: Dict) -> List[Tuple[str, str]]:
    """Valida una muestra del JSON contra el esquema de la BD"""
    issues = []
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        # Leer primera línea (formato JSONL)
        line = f.readline()
        if not line.strip():
            return [("ERROR", "Archivo JSON vacío")]
        
        data = json.loads(line)
        if not data.get('isSuccess') or not data.get('objects'):
            return [("ERROR", "Estructura JSON inválida")]
        
        product = data['objects'][0]  # Primer producto como muestra
    
    # Validar tabla PRODUCTS
    if 'products' in schema:
        # Campo title (NOT NULL)
        title = product.get('name', '')
        if not title:
            issues.append(("CRITICAL", "Campo 'name' (→ title) es NULL pero DB requiere NOT NULL"))
        elif 'title' in schema['products']:
            max_len = schema['products']['title'].get('max_length')
            if max_len and len(title) > max_len:
                issues.append(("ERROR", f"Campo 'name' ({len(title)} chars) excede límite de title ({max_len} chars)"))
        
        # Campo sku
        sku = product.get('sku', '')
        if sku and 'sku' in schema['products']:
            max_len = schema['products']['sku'].get('max_length')
            if max_len and len(sku) > max_len:
                issues.append(("ERROR", f"Campo 'sku' ({len(sku)} chars) excede límite DB ({max_len} chars)"))
        
        # Campo product_type
        ptype = product.get('type', '')
        if ptype and 'product_type' in schema['products']:
            max_len = schema['products']['product_type'].get('max_length')
            if max_len and len(ptype) > max_len:
                issues.append(("ERROR", f"Campo 'type' ({len(ptype)} chars) excede límite de product_type ({max_len} chars)"))
    
    # Validar tabla SUPPLIERS
    if 'suppliers' in schema:
        supplier = product.get('user', {})
        
        # Campo name
        name = supplier.get('name', '')
        if name and 'name' in schema['suppliers']:
            max_len = schema['suppliers']['name'].get('max_length')
            if max_len and len(name) > max_len:
                issues.append(("ERROR", f"Campo 'user.name' ({len(name)} chars) excede límite DB ({max_len} chars)"))
        
        # Campo store_name
        store_name = supplier.get('store_name', '')
        if store_name and 'store_name' in schema['suppliers']:
            max_len = schema['suppliers']['store_name'].get('max_length')
            if max_len and len(store_name) > max_len:
                issues.append(("ERROR", f"Campo 'user.store_name' ({len(store_name)} chars) excede límite DB ({max_len} chars)"))
        
        # Campo plan_name
        plan_name = supplier.get('plan', {}).get('name', '')
        if plan_name and 'plan_name' in schema['suppliers']:
            max_len = schema['suppliers']['plan_name'].get('max_length')
            if max_len and len(plan_name) > max_len:
                issues.append(("ERROR", f"Campo 'user.plan.name' ({len(plan_name)} chars) excede límite de plan_name ({max_len} chars)"))
    
    # Validar tabla WAREHOUSES
    if 'warehouses' in schema:
        # Verificar que city NO exista en esquema (debe estar eliminado)
        if 'city' in schema['warehouses']:
            issues.append(("CRITICAL", "Campo 'city' existe en DB pero NO está disponible en JSON - debe ser eliminado"))
    
    return issues

def print_schema_summary(schema: Dict):
    """Imprime un resumen del esquema de la BD"""
    print("\n" + "="*80)
    print("RESUMEN DEL ESQUEMA DE BASE DE DATOS")
    print("="*80 + "\n")
    
    for table_name, columns in sorted(schema.items()):
        print(f"\n📋 Tabla: {table_name.upper()}")
        print("-" * 80)
        print(f"{'Campo':<30} {'Tipo':<20} {'NULL?':<8} {'Max Len'}")
        print("-" * 80)
        
        for col_name, col_info in columns.items():
            nullable = "SÍ" if col_info['nullable'] else "NO"
            max_len = str(col_info['max_length']) if col_info['max_length'] else "-"
            print(f"{col_name:<30} {col_info['type']:<20} {nullable:<8} {max_len}")

def main():
    """Función principal"""
    print("\n🔍 VALIDADOR DE COMPATIBILIDAD JSON → DB\n")
    
    # 1. Obtener esquema de la BD
    print("1️⃣  Conectando a PostgreSQL y extrayendo esquema...")
    try:
        schema = get_db_schema()
        print(f"   ✅ Esquema cargado: {len(schema)} tablas encontradas")
    except Exception as e:
        print(f"   ❌ Error al conectar a la BD: {e}")
        return
    
    # 2. Mostrar resumen del esquema
    print_schema_summary(schema)
    
    # 3. Validar muestra de JSON
    json_sample = 'raw_data/raw_products_20251218.jsonl'
    if os.path.exists(json_sample):
        print(f"\n2️⃣  Validando muestra de JSON: {json_sample}")
        issues = validate_json_sample(json_sample, schema)
        
        if not issues:
            print("   ✅ No se encontraron incompatibilidades")
        else:
            print(f"   ⚠️  Se encontraron {len(issues)} problemas:")
            for severity, message in issues:
                icon = "🔴" if severity == "CRITICAL" else "⚠️ "
                print(f"   {icon} [{severity}] {message}")
    else:
        print(f"\n2️⃣  ⚠️  No se encontró archivo de muestra: {json_sample}")
        print("   Coloca un archivo JSONL en raw_data/ para validar")
    
    # 4. Guardar esquema a archivo
    output_file = 'dahell_db_schema_summary.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ESQUEMA DE BASE DE DATOS - DAHELL\n")
        f.write("=" * 80 + "\n\n")
        
        for table_name, columns in sorted(schema.items()):
            f.write(f"\nTabla: {table_name}\n")
            f.write("-" * 80 + "\n")
            for col_name, col_info in columns.items():
                nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                max_len = f" ({col_info['max_length']})" if col_info['max_length'] else ""
                f.write(f"  {col_name:<30} {col_info['type']}{max_len:<20} {nullable}\n")
    
    print(f"\n3️⃣  Esquema guardado en: {output_file}")
    print("\n" + "="*80)
    print("✅ VALIDACIÓN COMPLETA")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
