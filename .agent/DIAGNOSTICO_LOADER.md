# 🔍 DIAGNÓSTICO PROFUNDO: PROBLEMA DEL LOADER

**Fecha:** 2025-12-25 16:42:00  
**Problema:** Alta tasa de omisión (~45%) en el loader  
**Causa Raíz Identificada:** Transacciones abortadas en cascada

---

## 🐛 PROBLEMA IDENTIFICADO

### Error Principal:
```
InternalError: (psycopg2.errors.InFailedSqlTransaction) 
current transaction is aborted, commands ignored until end of transaction block
```

### Estadísticas:
- **Archivo:** raw_products_20251214.jsonl
- **Errores totales:** 26,574
- **Tipo de error:** 100% InternalError (transacción abortada)
- **Tasa de omisión:** ~45%

---

## 🔍 ANÁLISIS DEL PROBLEMA

### Flujo del Error:

```
1. Loader procesa registro A → OK
2. Loader procesa registro B → ERROR (causa desconocida)
3. Transacción se aborta
4. session.rollback() se ejecuta
5. Loader procesa registro C → FALLA (transacción abortada)
6. Loader procesa registro D → FALLA (transacción abortada)
7. ... todos los registros subsecuentes fallan en cascada
```

### Problema:
Después de `session.rollback()`, la transacción queda en estado "aborted" y **TODOS** los comandos SQL subsecuentes fallan con `InternalError`, incluso si son válidos.

---

## ❌ SOLUCIÓN INTENTADA (NO FUNCIONÓ)

### Código agregado:
```python
session.rollback()
session.begin()  # ← Esto no funciona con SQLAlchemy
```

### Por qué no funcionó:
SQLAlchemy maneja las transacciones automáticamente. Llamar a `session.begin()` manualmente puede causar conflictos.

---

## ✅ SOLUCIÓN CORRECTA

### Opción 1: Commit después de Rollback (RECOMENDADA)
```python
except Exception as e:
    stats["error"] += 1
    session.rollback()
    session.commit()  # Finaliza la transacción abortada
    # La próxima operación iniciará una nueva transacción automáticamente
```

### Opción 2: Usar Savepoints
```python
# Antes del try
savepoint = session.begin_nested()

try:
    self.ingest_record(record, session)
    stats["ok"] += 1
except Exception as e:
    savepoint.rollback()  # Solo rollback del savepoint, no de toda la transacción
    stats["error"] += 1
```

### Opción 3: Transacción Individual por Registro
```python
try:
    self.ingest_record(record, session)
    session.commit()  # Commit inmediato
    stats["ok"] += 1
except Exception as e:
    session.rollback()
    stats["error"] += 1
```

---

## 🎯 RECOMENDACIÓN

**Usar Opción 1** (Commit después de Rollback) porque:
- ✅ Simple y directo
- ✅ Compatible con SQLAlchemy
- ✅ No afecta el rendimiento significativamente
- ✅ Permite commits por lotes (cada 100 registros)

---

## 🔧 CÓDIGO CORREGIDO

```python
try:
    record = json.loads(line)
    self.ingest_record(record, session)
    stats["ok"] += 1
    
    # Commit por lotes
    if stats["ok"] % 100 == 0: 
        session.commit()
        self.print_batch_summary(filepath.name, stats)
        
except Exception as e:
    # Contar tipo de error
    error_type = type(e).__name__
    error_types[error_type] = error_types.get(error_type, 0) + 1
    
    # Guardar primeros 10 errores para análisis
    if len(error_samples) < 10:
        error_samples.append({
            "type": error_type,
            "message": str(e)[:200],
            "record_id": record.get("id") if isinstance(record, dict) else None
        })
    
    stats["error"] += 1
    session.rollback()
    session.commit()  # ← CRÍTICO: Finalizar transacción abortada
```

---

## 🚨 ERROR ORIGINAL (AÚN POR IDENTIFICAR)

El `InternalError` es un **error secundario** causado por la transacción abortada.

**Necesitamos identificar el error ORIGINAL** que causa el primer abort.

### Hipótesis:
1. **Constraint violation** (FK, unique, not null)
2. **Data type mismatch** (string donde se espera int)
3. **Encoding issues** (caracteres especiales)
4. **Null en campo requerido**

### Para identificarlo:
Necesitamos capturar el **primer error** antes de que la cascada comience.

---

## 📊 IMPACTO ESPERADO

### Antes del Fix:
- Tasa de éxito: ~55%
- Tasa de error: ~45%
- Productos insertados: 377

### Después del Fix (Estimado):
- Tasa de éxito: ~95%+ (solo errores reales)
- Tasa de error: ~5% (datos realmente inválidos)
- Productos insertados: ~6,000+ (de 6,831 scrapeados)

---

**Próximo paso:** Aplicar fix correcto y monitorear resultados
