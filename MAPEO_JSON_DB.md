# 📊 MAPEO COMPLETO: JSON Scraper → Base de Datos PostgreSQL

## 🎯 Propósito
Este documento mapea EXACTAMENTE cómo los datos del JSON del scraper se transforman e insertan en la base de datos PostgreSQL, permitiendo detectar incompatibilidades automáticamente.

---

## 📥 ESTRUCTURA DEL JSON DEL SCRAPER

```json
{
  "isSuccess": true,
  "objects": [
    {
      "id": 1835621,
      "sku": "Oximetro-11",
      "name": "Oxímetro Digital Pediátrico",
      "type": "SIMPLE",
      "user": {
        "id": 13615,
        "name": "Emdel",
        "plan": {
          "id": 4,
          "name": "SUPPLIER PREMIUM"
        },
        "store_name": "Emdel Colombia Mayorista"
      },
      "gallery": [
        {
          "url": null,
          "main": true,
          "urlS3": "colombia/products/1835621/174862298085.png"
        }
      ],
      "categories": [
        {"name": "Salud"},
        {"name": "Hogar"}
      ],
      "sale_price": 22000,
      "suggested_price": 42000,
      "warehouse_product": [
        {
          "id": 2078087,
          "stock": 91,
          "warehouse_id": 2302
        }
      ]
    }
  ]
}
```

---

## 🗄️ MAPEO A TABLAS DE BASE DE DATOS

### 1. **Tabla: `warehouses`**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `warehouse_id` | BIGINT | ✅ | `warehouse_product[].warehouse_id` | ID único de bodega |
| `first_seen_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |
| `last_seen_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |

**Campos ELIMINADOS:**
- ❌ `city` - NO disponible en JSON

**SQL de Inserción:**
```python
INSERT INTO warehouses (warehouse_id, first_seen_at, last_seen_at) 
VALUES (:wid, NOW(), NOW())
ON CONFLICT (warehouse_id) DO UPDATE SET last_seen_at = NOW()
```

---

### 2. **Tabla: `suppliers`**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `supplier_id` | BIGINT | ✅ | `user.id` | ID único de proveedor |
| `name` | VARCHAR(255) | ✅ | `user.name` | Nombre del proveedor |
| `store_name` | VARCHAR(255) | ❌ | `user.store_name` | Nombre de la tienda (puede ser null) |
| `plan_name` | VARCHAR(255) | ❌ | `user.plan.name` | Plan del proveedor |
| `is_verified` | BOOLEAN | ✅ | N/A (FALSE) | Generado automáticamente |
| `created_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |
| `updated_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |

**Ampliaciones aplicadas:**
- `name`: 100 → 255 caracteres ✅
- `store_name`: 100 → 255 caracteres ✅
- `plan_name`: 100 → 255 caracteres ✅

**SQL de Inserción:**
```python
INSERT INTO suppliers (supplier_id, name, store_name, plan_name, is_verified, created_at, updated_at)
VALUES (:sid, :name, :store, :plan, FALSE, NOW(), NOW())
ON CONFLICT (supplier_id) DO UPDATE
SET name = EXCLUDED.name, store_name = EXCLUDED.store_name, plan_name = EXCLUDED.plan_name, updated_at = NOW()
```

---

### 3. **Tabla: `products`**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `product_id` | BIGINT | ✅ | `id` | ID único de producto |
| `supplier_id` | BIGINT | ❌ | `user.id` | FK a suppliers |
| `sku` | VARCHAR(255) | ❌ | `sku` | SKU del producto |
| `title` | VARCHAR(500) | ✅ | `name` | Nombre/título del producto |
| `description` | TEXT | ❌ | `description` | Descripción (rara vez disponible) |
| `sale_price` | NUMERIC(10,2) | ❌ | `sale_price` | Precio de venta |
| `suggested_price` | NUMERIC(10,2) | ❌ | `suggested_price` | Precio sugerido |
| `product_type` | VARCHAR(255) | ❌ | `type` | Tipo: SIMPLE, VARIABLE |
| `url_image_s3` | TEXT | ❌ | `gallery[0].urlS3` | URL de imagen principal |
| `is_active` | BOOLEAN | ✅ | N/A (TRUE) | Generado automáticamente |
| `created_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |
| `updated_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |

**Ampliaciones aplicadas:**
- `sku`: 50 → 255 caracteres ✅
- `product_type`: 100 → 255 caracteres ✅

**Transformación de imagen:**
```python
def _extract_image(data):
    gallery = data.get("gallery", [])
    if gallery and isinstance(gallery, list):
        first = gallery[0]
        if isinstance(first, dict):
            raw = first.get("urlS3")
            if raw:
                return f"https://d39ru7awumhhs2.cloudfront.net/{quote(raw, safe='/')}"
    return None
```

**SQL de Inserción:**
```python
INSERT INTO products (
    product_id, supplier_id, sku, title, description,
    sale_price, suggested_price, product_type, 
    url_image_s3, is_active, created_at, updated_at
) VALUES (
    :pid, :sid, :sku, :title, :desc,
    :price, :sugg, :type, 
    :img, TRUE, NOW(), NOW()
)
ON CONFLICT (product_id) DO UPDATE
SET sale_price = EXCLUDED.sale_price,
    suggested_price = EXCLUDED.suggested_price,
    description = COALESCE(EXCLUDED.description, products.description),
    updated_at = NOW(),
    url_image_s3 = COALESCE(EXCLUDED.url_image_s3, products.url_image_s3)
```

---

### 4. **Tabla: `categories`**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `id` | SERIAL | ✅ | N/A (AUTO) | ID auto-generado |
| `name` | VARCHAR(100) | ✅ | `categories[].name` | Nombre de categoría |

**SQL de Inserción:**
```python
INSERT INTO categories (name)
VALUES (:name)
ON CONFLICT (name) DO NOTHING
```

---

### 5. **Tabla: `product_categories` (Many-to-Many)**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `product_id` | BIGINT | ✅ | `id` | FK a products |
| `category_id` | INT | ✅ | categories[].name → ID | FK a categories |

**SQL de Inserción:**
```python
INSERT INTO product_categories (product_id, category_id)
VALUES (:pid, :cid)
ON CONFLICT (product_id, category_id) DO NOTHING
```

---

### 6. **Tabla: `product_stock_log`**

| Campo DB | Tipo | NOT NULL | JSON Path | Comentario |
|----------|------|----------|-----------|------------|
| `product_id` | BIGINT | ✅ | `id` | FK a products |
| `warehouse_id` | BIGINT | ✅ | `warehouse_product[].warehouse_id` | FK a warehouses |
| `stock_qty` | INT | ❌ | `warehouse_product[].stock` | Cantidad en stock |
| `recorded_at` | TIMESTAMP | ✅ | N/A (NOW()) | Generado automáticamente |

**SQL de Inserción:**
```python
INSERT INTO product_stock_log (product_id, warehouse_id, stock_qty)
VALUES (:pid, :wid, :qty)
```

---

## 🔍 GUÍA DE VALIDACIÓN

### Checklist de Verificación antes de Modificar Loader

1. **Verificar campos NOT NULL:**
   ```sql
   SELECT table_name, column_name 
   FROM information_schema.columns 
   WHERE is_nullable='NO' AND table_schema='public';
   ```

2. **Verificar límites de VARCHAR:**
   ```sql
   SELECT table_name, column_name, character_maximum_length 
   FROM information_schema.columns 
   WHERE data_type LIKE '%char%' AND table_schema='public';
   ```

3. **Comparar con JSON del scraper:**
   - ¿El campo existe en el JSON?
   - ¿El valor siempre está presente o puede ser null?
   - ¿Qué tan largo puede ser el valor?

4. **Probar con producto de ejemplo:**
   ```python
   # Extraer un producto del JSON
   product = json.loads(raw_line)
   
   # Verificar que todos los campos requeridos existan
   assert product.get("id") is not None
   assert product.get("name") is not None
   ```

---

## ⚠️ CAMPOS ELIMINADOS DEL ESQUEMA

| Tabla | Campo | Razón |
|-------|-------|-------|
| `warehouses` | `city` | No disponible en JSON del scraper |

---

## 🆕 CAMPOS AGREGADOS AUTOMÁTICAMENTE

| Tabla | Campo | Valor | Razón |
|-------|-------|-------|-------|
| `warehouses` | `first_seen_at` | NOW() | Timestamp de primera aparición |
| `warehouses` | `last_seen_at` | NOW() | Timestamp de última actualización |
| `suppliers` | `is_verified` | FALSE | Estado de verificación |
| `suppliers` | `created_at` | NOW() | Timestamp de creación |
| `suppliers` | `updated_at` | NOW() | Timestamp de última actualización |
| `products` | `is_active` | TRUE | Estado activo por defecto |
| `products` | `created_at` | NOW() | Timestamp de creación |
| `products` | `updated_at` | NOW() | Timestamp de última actualización |

---

## 📋 RESUMEN DE COMPATIBILIDAD

✅ **Compatible:**
- Todos los campos requeridos tienen origen en JSON o valor por defecto
- Límites de VARCHAR ampliados para acomodar datos reales
- Campos NOT NULL están cubiertos

❌ **Incompatible (Corregido):**
- ~~`warehouses.city`~~ → ELIMINADO
- ~~VARCHAR límites pequeños~~ → AMPLIADOS a 255

---

**Última actualización:** 2025-12-19  
**Generado por:** Sistema de Auditoría Dahell
