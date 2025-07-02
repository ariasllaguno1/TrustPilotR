# GitHub Actions para TrustPilot Analysis

Esta documentación explica cómo usar los workflows de GitHub Actions para automatizar el análisis de reseñas de TrustPilot.

## 📋 Resumen de Workflows Disponibles

### 1. 🚀 **trustpilot_analysis.yml** (RECOMENDADO)
- **Archivo:** `.github/workflows/trustpilot_analysis.yml`
- **Script:** `trustpilot_analysis.py`
- **Descripción:** Workflow optimizado que usa un script Python para análisis rápido y eficiente
- **Ventajas:** Más rápido, menos dependencias, mejor manejo de errores

### 2. 📓 **analysis.yml** (Alternativo)
- **Archivo:** `.github/workflows/analysis.yml`
- **Notebook:** `TrustPilotAnalysis.ipynb`
- **Descripción:** Workflow que ejecuta el notebook Jupyter usando papermill
- **Ventajas:** Mantiene la interactividad del notebook, útil para desarrollo

## 🛠️ Configuración Inicial

### 1. Configurar API Key de OpenRouter

1. Ve a [OpenRouter](https://openrouter.ai/keys) y obtén tu API key
2. En tu repositorio de GitHub, ve a **Settings** > **Secrets and variables** > **Actions**
3. Haz clic en **New repository secret**
4. Nombre: `OPENROUTER_API_KEY`
5. Valor: Tu API key de OpenRouter
6. Haz clic en **Add secret**

### 2. Subir archivo CSV

Asegúrate de que tu archivo CSV de reseñas esté en la raíz del repositorio (ej: `test.csv`).

## 🚀 Cómo Ejecutar el Análisis

### Opción 1: Workflow Optimizado (Script Python)

1. Ve a la pestaña **Actions** en tu repositorio
2. Selecciona **"Análisis TrustPilot con Script Python"**
3. Haz clic en **"Run workflow"**
4. Configura los parámetros:
   - **CSV file:** Nombre del archivo (ej: `test.csv`)
   - **Batch size:** Número de reseñas por lote (recomendado: 10)
   - **Max reviews:** Límite de reseñas (vacío = todas)
   - **Model:** Modelo de IA (default: `google/gemini-2.5-flash`)
5. Haz clic en **"Run workflow"**

### Opción 2: Workflow con Notebook

1. Ve a la pestaña **Actions** en tu repositorio
2. Selecciona **"Análisis TrustPilot con LLM"**
3. Sigue los mismos pasos que la Opción 1

## 📊 Parámetros de Configuración

| Parámetro | Descripción | Valores recomendados |
|-----------|-------------|---------------------|
| **csv_file** | Archivo CSV a analizar | `test.csv`, `reviews.csv` |
| **batch_size** | Reseñas por lote | `5-15` (10 recomendado) |
| **max_reviews** | Límite de reseñas | Vacío (todas), `50`, `100` |
| **openrouter_model** | Modelo de IA | `google/gemini-2.5-flash` (rápido)<br>`openai/gpt-3.5-turbo` (preciso) |

## 📈 Resultados del Análisis

### Archivos Generados

- **`trustpilot_analyzed_YYYYMMDD_HHMMSS.csv`** - Resultados con timestamp
- **`trustpilot_analyzed_latest.csv`** - Último análisis (backup)

### Campos Analizados

El análisis genera los siguientes campos para cada reseña:

1. **language** - Idioma detectado (es, en, fr, etc.)
2. **sentiment** - Sentimiento (Positivo, Negativo, Neutro)
3. **sentiment_score** - Puntuación de sentimiento (-1 a +1)
4. **emotion** - Emoción detectada (joy, anger, sadness, etc.)
5. **emotion_intensity** - Intensidad emocional (1-5)
6. **customer_gender** - Género inferido (masculino, femenino, unknown)
7. **main_topic** - Tema principal de la reseña
8. **keywords** - Palabras clave relevantes
9. **customer_type** - Tipo de cliente (Promotor, Crítico, etc.)
10. **tourist_type** - Tipo de turista (ocio, cultural, etc.)
11. **group_type** - Tipo de grupo (familiar, pareja, etc.)

### Estadísticas Generadas

El workflow genera automáticamente:
- Distribución de sentimientos
- Temas más frecuentes
- Tipos de turista
- Emociones detectadas
- Resumen de errores

## 📁 Descargar Resultados

1. Ve a la ejecución del workflow en **Actions**
2. Desplázate hacia abajo hasta **Artifacts**
3. Descarga **trustpilot-analysis-results**
4. Extrae el archivo ZIP para obtener los CSV

## ⚙️ Uso Local del Script

También puedes ejecutar el script localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar análisis
python trustpilot_analysis.py test.csv --api-key tu-api-key

# Con parámetros opcionales
python trustpilot_analysis.py test.csv \
  --model google/gemini-2.5-flash \
  --batch-size 10 \
  --max-reviews 50
```

### Argumentos del Script

```bash
python trustpilot_analysis.py <archivo_csv> [opciones]

Opciones:
  --api-key         API key de OpenRouter
  --model           Modelo a usar (default: google/gemini-2.5-flash)
  --batch-size      Tamaño del lote (default: 10)
  --max-reviews     Máximo de reseñas a analizar
  --verbose, -v     Modo detallado
```

## 🔧 Solución de Problemas

### Error: "OPENROUTER_API_KEY no está configurada"
- Verifica que hayas agregado el secret correctamente
- El nombre debe ser exactamente `OPENROUTER_API_KEY`

### Error: "No se encontró el archivo CSV"
- Asegúrate de que el archivo esté en la raíz del repositorio
- Verifica que el nombre del archivo sea correcto

### Análisis muy lento
- Reduce el `batch_size` a 5-8
- Usa un modelo más rápido: `google/gemini-2.5-flash`
- Limita el número de reseñas con `max_reviews`

### Rate limit de API
- Aumenta las pausas entre peticiones (automático)
- Reduce el `batch_size`
- Usa un plan de pago en OpenRouter para mayor límite

## 💡 Consejos de Optimización

1. **Para pruebas:** Usa `max_reviews: 20-50`
2. **Para producción:** Usa `batch_size: 10` y sin límite
3. **Para rapidez:** Usa `google/gemini-2.5-flash`
4. **Para precisión:** Usa `openai/gpt-3.5-turbo`
5. **Monitoreo:** Revisa los logs en GitHub Actions

## 📊 Modelos Disponibles

| Modelo | Velocidad | Costo | Precisión | Recomendado para |
|--------|-----------|-------|-----------|------------------|
| `google/gemini-2.5-flash` | ⚡⚡⚡ | 💰 | ⭐⭐⭐ | Análisis masivo |
| `openai/gpt-3.5-turbo` | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | Análisis preciso |
| `meta-llama/llama-3-8b-instruct` | ⚡ | 💰 | ⭐⭐ | Análisis económico |

## 🔄 Actualizaciones Futuras

Para mantenerte actualizado:
1. Watch este repositorio para notificaciones
2. Revisa las [releases](../../releases) para nuevas versiones
3. Actualiza tu API key si es necesario

## ❓ Soporte

Si tienes problemas:
1. Revisa esta documentación
2. Revisa los logs en GitHub Actions
3. Crea un [issue](../../issues) con detalles del error 