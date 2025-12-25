# 🔧 COMANDOS ÚTILES PARA MONITOREO DEL VECTORIZER

## 📊 Verificación de Estado

### Ver estado de todos los contenedores
```bash
docker ps -a
```

### Ver estado específico del vectorizer
```bash
docker ps -a --filter "name=dahell_vectorizer"
```

### Ver logs en tiempo real
```bash
docker logs -f dahell_vectorizer
```

### Ver últimas 50 líneas de logs
```bash
docker logs dahell_vectorizer --tail 50
```

### Ver logs del archivo local
```bash
Get-Content logs/vectorizer.log -Wait -Tail 20
```

---

## 🔍 Diagnóstico de Base de Datos

### Contar productos totales y con imágenes
```bash
docker exec dahell_db psql -U dahell_admin -d dahell_db -c "SELECT COUNT(*) as total_products, COUNT(url_image_s3) as with_images FROM products;"
```

### Contar productos vectorizados
```bash
docker exec dahell_db psql -U dahell_admin -d dahell_db -c "SELECT COUNT(*) as vectorized FROM product_embeddings WHERE embedding_visual IS NOT NULL;"
```

### Ver productos pendientes de vectorizar
```bash
docker exec dahell_db psql -U dahell_admin -d dahell_db -c "
SELECT COUNT(*) as pending
FROM products p
LEFT JOIN product_embeddings pe ON p.product_id = pe.product_id
WHERE p.url_image_s3 IS NOT NULL 
AND p.url_image_s3 != ''
AND (pe.product_id IS NULL OR pe.embedding_visual IS NULL);"
```

### Ver últimos productos vectorizados
```bash
docker exec dahell_db psql -U dahell_admin -d dahell_db -c "
SELECT p.product_id, p.title, pe.processed_at
FROM products p
JOIN product_embeddings pe ON p.product_id = pe.product_id
WHERE pe.embedding_visual IS NOT NULL
ORDER BY pe.processed_at DESC
LIMIT 10;"
```

---

## 🐛 Verificación de Dependencias

### Verificar que sentencepiece está instalado
```bash
docker exec dahell_vectorizer pip list | grep -i sentence
```

### Verificar todas las dependencias de ML
```bash
docker exec dahell_vectorizer pip list | grep -E "(torch|transformers|sentence)"
```

### Verificar versión de Python
```bash
docker exec dahell_vectorizer python --version
```

### Verificar que PyTorch detecta CUDA
```bash
docker exec dahell_vectorizer python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## 🔄 Gestión del Servicio

### Iniciar vectorizer
```bash
docker-compose --profile workers up -d vectorizer
```

### Detener vectorizer
```bash
docker-compose stop vectorizer
```

### Reiniciar vectorizer
```bash
docker-compose --profile workers restart vectorizer
```

### Ver logs durante el inicio
```bash
docker-compose --profile workers up vectorizer
```

### Reconstruir imagen (después de cambios en código)
```bash
docker-compose build vectorizer
```

### Reconstruir sin cache (limpieza completa)
```bash
docker-compose build --no-cache vectorizer
```

---

## 🗑️ Limpieza y Mantenimiento

### Limpiar cache de HuggingFace (si está corrupto)
```bash
rm -rf cache_huggingface/*
```

### Ver tamaño del cache
```bash
du -sh cache_huggingface/
```

### Eliminar contenedor y volúmenes
```bash
docker-compose down vectorizer
docker volume prune
```

### Ver uso de espacio en disco de Docker
```bash
docker system df
```

---

## 📈 Monitoreo de Rendimiento

### Ver uso de CPU y memoria del contenedor
```bash
docker stats dahell_vectorizer --no-stream
```

### Ver uso de memoria en tiempo real
```bash
docker stats dahell_vectorizer
```

### Ejecutar comando dentro del contenedor
```bash
docker exec -it dahell_vectorizer bash
```

### Ver variables de entorno del contenedor
```bash
docker exec dahell_vectorizer env | grep -E "(POSTGRES|HF_HOME)"
```

---

## 🧪 Testing y Validación

### Probar conexión a la base de datos desde el contenedor
```bash
docker exec dahell_vectorizer python -c "
import psycopg2
import os
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
print('✅ Conexión exitosa')
conn.close()
"
```

### Probar carga del modelo SigLIP
```bash
docker exec dahell_vectorizer python -c "
from transformers import AutoProcessor, SiglipModel
import torch
print('Cargando modelo...')
model = SiglipModel.from_pretrained('google/siglip-so400m-patch14-384')
processor = AutoProcessor.from_pretrained('google/siglip-so400m-patch14-384')
print('✅ Modelo cargado correctamente')
"
```

### Verificar que puede procesar una imagen
```bash
docker exec dahell_vectorizer python -c "
from PIL import Image
import requests
from io import BytesIO
from transformers import AutoProcessor, SiglipModel
import torch

# Descargar imagen de prueba
url = 'https://via.placeholder.com/384'
response = requests.get(url)
img = Image.open(BytesIO(response.content)).convert('RGB')

# Cargar modelo
model = SiglipModel.from_pretrained('google/siglip-so400m-patch14-384')
processor = AutoProcessor.from_pretrained('google/siglip-so400m-patch14-384')

# Procesar
inputs = processor(images=[img], return_tensors='pt')
with torch.no_grad():
    features = model.get_image_features(**inputs)
    
print(f'✅ Embedding generado: shape={features.shape}')
"
```

---

## 🚨 Troubleshooting

### Si el contenedor no inicia
1. Ver logs completos:
   ```bash
   docker logs dahell_vectorizer
   ```

2. Verificar que la imagen se construyó correctamente:
   ```bash
   docker images | grep dahell
   ```

3. Verificar que el puerto de DB es accesible:
   ```bash
   docker exec dahell_vectorizer nc -zv db 5432
   ```

### Si el modelo no se descarga
1. Verificar conectividad a internet:
   ```bash
   docker exec dahell_vectorizer ping -c 3 huggingface.co
   ```

2. Verificar permisos del cache:
   ```bash
   ls -la cache_huggingface/
   ```

3. Descargar modelo manualmente:
   ```bash
   docker exec dahell_vectorizer python -c "
   from transformers import AutoProcessor, SiglipModel
   model = SiglipModel.from_pretrained('google/siglip-so400m-patch14-384')
   processor = AutoProcessor.from_pretrained('google/siglip-so400m-patch14-384')
   print('✅ Descarga completa')
   "
   ```

### Si hay problemas de memoria
1. Reducir batch size en `vectorizer.py` (ya está en 50)
2. Verificar memoria disponible:
   ```bash
   docker exec dahell_vectorizer free -h
   ```

3. Limitar memoria del contenedor en docker-compose.yml:
   ```yaml
   vectorizer:
     deploy:
       resources:
         limits:
           memory: 4G
   ```

---

## 📝 Workflow Completo de Corrección

```bash
# 1. Detener servicio actual
docker-compose stop vectorizer

# 2. Reconstruir imagen con nuevas dependencias
docker-compose build vectorizer

# 3. Limpiar cache si es necesario
# rm -rf cache_huggingface/*

# 4. Iniciar servicio
docker-compose --profile workers up -d vectorizer

# 5. Monitorear logs
docker logs -f dahell_vectorizer

# 6. Verificar que está procesando
# (En otra terminal)
docker exec dahell_db psql -U dahell_admin -d dahell_db -c "
SELECT COUNT(*) FROM product_embeddings WHERE embedding_visual IS NOT NULL;"
```

---

**Generado por Antigravity AI**  
**Última actualización:** 2025-12-25
