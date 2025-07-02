# TrustPilot Scraper - GitHub Actions

## 🤖 Ejecutar el scraper automáticamente en GitHub

Este proyecto permite hacer scraping de reseñas de TrustPilot (categoría Viajes y Vacaciones) directamente desde GitHub Actions, sin necesidad de ejecutarlo en tu laptop.

## 🚀 Cómo usar

### 1. Configuración inicial (solo la primera vez)

1. **Fork este repositorio** o clónalo en tu cuenta de GitHub
2. Ve a la pestaña **"Actions"** de tu repositorio
3. Si es la primera vez, acepta habilitar GitHub Actions

### 2. Ejecutar el scraper

1. **Ve a la pestaña "Actions"** de tu repositorio
2. **Selecciona "Ejecutar TrustPilotScraper"** en la lista de workflows
3. **Haz clic en "Run workflow"** (botón verde a la derecha)
4. **Configura los parámetros:**
   - **Empresas máximas**: Cuántas empresas procesar (por defecto: 100)
   - **Páginas de reseñas por empresa**: Cuántas páginas de reseñas extraer de cada empresa (por defecto: 10)
   - **Páginas de categoría**: Cuántas páginas de la categoría recorrer para encontrar empresas (por defecto: 10)
5. **Haz clic en "Run workflow"**

### 3. Monitorear el progreso

- El workflow aparecerá en la lista con un ícono amarillo ⭕ (ejecutándose) o verde ✅ (completado)
- Haz clic en la ejecución para ver el progreso en tiempo real
- El proceso puede tomar desde 30 minutos hasta varias horas dependiendo de los parámetros

### 4. Descargar los resultados

Una vez completado el workflow:

1. **Ve a la ejecución completada** en la pestaña Actions
2. **Busca la sección "Artifacts"** al final de la página
3. **Descarga los archivos:**
   - `csv-files`: Todos los archivos CSV con las reseñas
   - `checkpoints`: Archivos de progreso (por si quieres reanudar)
   - `executed-notebook`: El notebook ejecutado con resultados
   - `error-logs`: Logs de errores si los hubo

## 📊 Qué contienen los archivos

### Archivos CSV principales:
- `trustpilot_consolidated_YYYYMMDD_HHMMSS.csv`: **Archivo principal** con todas las reseñas
- `companies_processed_YYYYMMDD_HHMMSS.csv`: Lista de empresas procesadas
- `results/reviews_[dominio]_YYYYMMDD_HHMMSS.csv`: Reseñas individuales por empresa

### Columnas del dataset:
- **Información básica**: `review_id`, `domain`, `company_name`, `categories`, `subcategories`
- **Detalles de la reseña**: `review_date`, `customer_name`, `customer_score`, `review_text`
- **Para análisis posterior**: `language`, `sentiment`, `emotion`, `customer_gender`, `main_topic`, `keywords`, etc.

## ⚙️ Configuración avanzada

### Límites recomendados:

| Uso | Empresas | Páginas/empresa | Páginas categoría | Tiempo aprox. |
|-----|----------|-----------------|-------------------|---------------|
| **Prueba rápida** | 10 | 3 | 3 | 10-15 min |
| **Dataset pequeño** | 50 | 10 | 10 | 1-2 horas |
| **Dataset mediano** | 200 | 20 | 20 | 3-4 horas |
| **Dataset grande** | 500+ | 50+ | 50+ | 5-6 horas |

### Límites de GitHub Actions:
- **Tiempo máximo**: 6 horas por ejecución
- **Almacenamiento**: Los artefactos se conservan 30 días
- **Concurrencia**: Solo una ejecución simultánea

## 🔧 Archivos del proyecto

- `.github/workflows/scraper.yml`: Configuración del workflow de GitHub Actions
- `scraper_github_actions.py`: Scraper optimizado para ejecutar en CI/CD
- `TrustPilotScraper.ipynb`: Notebook original para ejecutar localmente
- `requirements.txt`: Dependencias de Python

## ⚠️ Consideraciones importantes

### Términos de uso:
- **Respeta los términos de servicio** de TrustPilot
- **Uso académico/investigación**: Este scraper está diseñado para fines educativos
- **Rate limiting**: El scraper incluye delays aleatorios para ser respetuoso

### Limitaciones técnicas:
- **Modo headless**: Se ejecuta sin interfaz gráfica en servidores de GitHub
- **Sin persistencia**: Los checkpoints se pierden entre ejecuciones (solo útiles si el workflow falla)
- **Detección anti-bot**: TrustPilot puede bloquear solicitudes automatizadas

## 🆘 Solución de problemas

### El workflow falla:
1. **Revisa los logs** en la pestaña Actions
2. **Reduce los parámetros** (menos empresas/páginas)
3. **Espera un tiempo** antes de volver a ejecutar

### No se generan archivos CSV:
- Posible bloqueo de TrustPilot
- Cambios en la estructura de la página
- Revisa los logs de errores en los artefactos

### El workflow se detiene por timeout:
- Reduce el número de empresas o páginas
- GitHub Actions tiene un límite de 6 horas

## 🎯 Próximos pasos

Una vez que tengas los datos:

1. **Análisis básico**: Usa pandas para explorar los datos
2. **Análisis de sentimientos**: Usa las columnas preparadas para LLM
3. **Visualizaciones**: Crea gráficos con matplotlib/seaborn
4. **Machine Learning**: Entrena modelos para clasificación de reseñas

## 📝 Ejemplo de uso en Python

```python
import pandas as pd

# Cargar los datos descargados
df = pd.read_csv('trustpilot_consolidated_YYYYMMDD_HHMMSS.csv')

# Exploración básica
print(f"Total de reseñas: {len(df)}")
print(f"Empresas únicas: {df['company_name'].nunique()}")
print(f"Distribución de puntuaciones:")
print(df['customer_score'].value_counts().sort_index())

# Filtrar reseñas por puntuación
reseñas_positivas = df[df['customer_score'] >= 4]
reseñas_negativas = df[df['customer_score'] <= 2]

# Análisis por empresa
empresas_top = df.groupby('company_name').agg({
    'customer_score': 'mean',
    'review_id': 'count'
}).rename(columns={'review_id': 'num_reviews'}).sort_values('num_reviews', ascending=False)

print(empresas_top.head())
```

---

## 📧 Soporte

Si tienes problemas o preguntas, revisa:
1. Los logs del workflow en GitHub Actions
2. Los archivos de error en los artefactos
3. La documentación de los notebooks originales 