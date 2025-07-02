# 📊 GitHub Actions - Análisis de Reseñas TrustPilot

Este workflow automatiza el análisis de reseñas de TrustPilot usando modelos de lenguaje (LLM) a través de OpenRouter.

## 🚀 Configuración inicial

### 1. Configurar API Key de OpenRouter

1. Obtén tu API key de [OpenRouter](https://openrouter.ai/keys)
2. Ve a tu repositorio en GitHub
3. Navega a **Settings** > **Secrets and variables** > **Actions**
4. Crea un nuevo secret llamado `OPENROUTER_API_KEY`
5. Pega tu API key como valor

### 2. Preparar archivo CSV

Asegúrate de que tu archivo CSV tenga las siguientes columnas:
- `review_text`: Texto de la reseña
- `customer_name`: Nombre del cliente
- Otras columnas opcionales (se preservarán en el resultado)

## 📋 Ejecución del workflow

### Pasos para ejecutar:

1. Ve a la pestaña **Actions** de tu repositorio
2. Selecciona el workflow **"Análisis TrustPilot con LLM"**
3. Haz clic en **"Run workflow"**
4. Configura los parámetros:

#### Parámetros disponibles:

| Parámetro | Descripción | Valor por defecto | Ejemplo |
|-----------|-------------|-------------------|---------|
| `csv_file` | Nombre del archivo CSV a analizar | `test.csv` | `reviews_data.csv` |
| `batch_size` | Número de reseñas procesadas por lote | `10` | `5` (para APIs lentas) |
| `max_reviews` | Máximo de reseñas a analizar | *(todas)* | `100` |
| `openrouter_model` | Modelo de LLM a usar | `google/gemini-2.5-flash` | `openai/gpt-3.5-turbo` |

### Modelos recomendados:

- **Rápido y económico**: `google/gemini-2.5-flash`
- **Equilibrado**: `openai/gpt-3.5-turbo`
- **Más avanzado**: `openai/gpt-4o-mini`
- **Open source**: `meta-llama/llama-3-8b-instruct`

## 📊 Resultados del análisis

El análisis genera las siguientes columnas adicionales:

| Campo | Descripción | Valores posibles |
|-------|-------------|------------------|
| `language` | Idioma detectado | `es`, `en`, `fr`, `de`, etc. |
| `sentiment` | Sentimiento general | `Positivo`, `Negativo`, `Neutro` |
| `sentiment_score` | Puntuación de sentimiento | `-1.0` a `+1.0` |
| `emotion` | Emoción principal | `joy`, `anger`, `sadness`, etc. |
| `emotion_intensity` | Intensidad emocional | `1` (leve) a `5` (muy intensa) |
| `customer_gender` | Género inferido del nombre | `masculino`, `femenino`, `unknown` |
| `main_topic` | Tema principal | `Atención al cliente`, `Limpieza`, etc. |
| `keywords` | Palabras clave | `excelente,servicio,amable` |
| `customer_type` | Tipo de cliente | `Promotor`, `Leal`, `Crítico`, etc. |
| `tourist_type` | Tipo de turista | `Turista de ocio`, `cultural`, etc. |
| `group_type` | Tipo de grupo | `familiar`, `pareja`, `solitario`, etc. |

## 📁 Archivos generados

Al finalizar, encontrarás en los **Artifacts**:

### `analysis-results`
- `trustpilot_analyzed_[timestamp].csv`: Archivo con análisis completo
- `trustpilot_analyzed_latest.csv`: Última versión del análisis
- `analysis_results.html`: Reporte visual (si se generó)
- `TrustPilotAnalysis_executed.ipynb`: Notebook ejecutado

### `analysis-logs`
- `analysis_params.yaml`: Parámetros utilizados
- Logs de ejecución y errores

## 🔧 Personalización avanzada

### Modificar el prompt de análisis

Para personalizar cómo se analizan las reseñas, edita la función `crear_prompt_analisis()` en el notebook `TrustPilotAnalysis.ipynb`.

### Agregar nuevos campos de análisis

1. Modifica la lista `CAMPOS_ANALISIS` en el notebook
2. Actualiza el prompt para incluir el nuevo campo
3. Ajusta la función de procesamiento según sea necesario

### Cambiar modelo de LLM

Puedes usar cualquier modelo disponible en OpenRouter:
- Modelos OpenAI: `openai/gpt-4o`, `openai/gpt-3.5-turbo`
- Modelos Google: `google/gemini-pro`, `google/gemini-2.5-flash`
- Modelos Anthropic: `anthropic/claude-3-sonnet`
- Modelos Meta: `meta-llama/llama-3-70b-instruct`

## ⚠️ Consideraciones importantes

### Costos
- Los modelos tienen diferentes precios por token
- `google/gemini-2.5-flash` es uno de los más económicos
- Puedes limitar el número de reseñas con `max_reviews`

### Límites de tiempo
- Timeout máximo: 3 horas
- Para datasets grandes, considera dividir en múltiples ejecuciones

### Rate limits
- El workflow incluye pausas automáticas entre peticiones
- Ajusta `batch_size` si encuentras errores de rate limiting

## 🐛 Resolución de problemas

### Error: "OPENROUTER_API_KEY no está configurada"
- Verifica que el secret esté creado correctamente
- Asegúrate de que el nombre sea exactamente `OPENROUTER_API_KEY`

### Error: "No se encontró el archivo CSV"
- Confirma que el archivo esté en la raíz del repositorio
- Verifica que el nombre del archivo sea correcto

### Análisis incompleto
- Revisa los logs en los artifacts
- Considera reducir `batch_size` o usar un modelo más rápido
- Algunos modelos pueden ser inestables con prompts complejos

### Resultados inconsistentes
- Prueba con `temperature: 0.1` (ya configurado)
- Considera usar un modelo más avanzado
- Revisa que el prompt sea claro y específico

## 📈 Ejemplo de uso

```yaml
# Configuración recomendada para dataset pequeño (< 100 reseñas)
csv_file: "mi_dataset.csv"
batch_size: 10
max_reviews: ""  # Procesar todas
openrouter_model: "google/gemini-2.5-flash"

# Configuración para dataset grande (> 500 reseñas)
csv_file: "dataset_grande.csv"
batch_size: 5
max_reviews: 200  # Procesar solo las primeras 200
openrouter_model: "google/gemini-2.5-flash"
```

## 🔄 Ejecución programada

Para ejecutar automáticamente, puedes agregar un trigger `schedule` al workflow:

```yaml
on:
  schedule:
    - cron: '0 2 * * 1'  # Cada lunes a las 2 AM
  workflow_dispatch:  # Mantener ejecución manual
```

---

💡 **Tip**: Siempre revisa los artifacts generados para verificar que el análisis se completó correctamente antes de usar los resultados.