#!/usr/bin/env python3
"""
TrustPilot Analysis Script
Análisis automatizado de reseñas usando LLM de OpenRouter
"""

import pandas as pd
import numpy as np
import requests
import json
from tqdm import tqdm
import time
from datetime import datetime
import os
import sys
import argparse
from typing import Dict, List, Optional, Tuple

# Configuración por defecto
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_BATCH_SIZE = 10
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Definir los campos esperados en la respuesta del modelo (en orden)
CAMPOS_ANALISIS = [
    "language", "sentiment", "sentiment_score", "emotion", "emotion_intensity", "customer_gender",
    "main_topic", "keywords", "customer_type", "tourist_type", "group_type"
]

class TrustPilotAnalyzer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """Inicializar el analizador con configuración de API"""
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/actions",
            "X-Title": "TrustPilot Analysis"
        }
        self.review_text_col = None
        self.customer_name_col = None
        
    def detectar_columnas(self, df: pd.DataFrame) -> bool:
        """Detectar automáticamente las columnas de texto y nombre"""
        # Buscar columna de review_text
        texto_columnas = [col for col in df.columns if 'review' in col.lower() and 'text' in col.lower()]
        nombre_columnas = [col for col in df.columns if 'customer' in col.lower() and 'name' in col.lower()]
        
        if not texto_columnas:
            # Buscar alternativas
            texto_columnas = [col for col in df.columns if 'text' in col.lower()]
            
        if not nombre_columnas:
            # Buscar alternativas
            nombre_columnas = [col for col in df.columns if 'name' in col.lower()]
        
        if texto_columnas and nombre_columnas:
            self.review_text_col = texto_columnas[0]
            self.customer_name_col = nombre_columnas[0]
            print(f"✅ Columnas detectadas:")
            print(f"   - Texto de reseña: '{self.review_text_col}'")
            print(f"   - Nombre del cliente: '{self.customer_name_col}'")
            return True
        else:
            print("❌ No se pudieron detectar las columnas necesarias")
            print(f"Columnas disponibles: {list(df.columns)}")
            return False

    def cargar_datos(self, csv_path: str) -> pd.DataFrame:
        """Cargar y limpiar los datos del CSV"""
        print(f"📂 Cargando datos desde: {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"El archivo {csv_path} no existe")
        
        # Cargar CSV
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        
        print(f"📊 Total de reseñas cargadas: {len(df)}")
        
        # Detectar columnas
        if not self.detectar_columnas(df):
            raise ValueError("No se pudieron detectar las columnas necesarias")
        
        # Limpiar datos
        df_original_len = len(df)
        df = df.dropna(subset=[self.review_text_col])
        df = df[df[self.review_text_col].astype(str).str.strip() != '']
        
        print(f"📋 Limpieza de datos:")
        print(f"   - Reseñas originales: {df_original_len}")
        print(f"   - Reseñas después de limpieza: {len(df)}")
        print(f"   - Reseñas eliminadas: {df_original_len - len(df)}")
        
        # Inicializar columna 'analyzed' si no existe
        if 'analyzed' not in df.columns:
            df['analyzed'] = False
            
        pendientes = (df['analyzed'] == False).sum()
        print(f"   - Reseñas pendientes de analizar: {pendientes}")
        
        return df

    def crear_prompt_analisis(self, review_text: str, customer_name: str) -> str:
        """Crear el prompt para analizar una reseña"""
        return f"""
Eres un analizador especializado en evaluación de reseñas turísticas y análisis de sentimientos. Para cada texto que recibas, deberás analizar y proporcionar la siguiente información separada por el delimitador "|":

RESEÑA A ANALIZAR:
Texto: {review_text}
Cliente: {customer_name}

ANÁLISIS REQUERIDO (responde cada campo separado por "|"):

0. Language: Clasifica como "es", "en", "fr", "de", "it", "pt", "nl", "ru", "tr", "ar", "zh", "ja", "ko", "other"
1. Sentiment: Clasifica como "Positivo", "Negativo" o "Neutro"
2. Sentiment_score: Evalúa en escala de -1 a +1 (-1=extremadamente negativo, 0=neutro, +1=extremadamente positivo)
3. Emotion: Identifica una emoción (joy, surprise, neutral, sadness, disgust, anger, fear)
4. Emotion_intensity: Intensidad de 1-5 (1=muy leve, 5=muy intensa)
5. Customer_gender: Basado en el nombre (masculino, femenino, unknown)
6. Topic: Tema principal (Atención al cliente, Limpieza, Instalaciones, Relación calidad-precio, Servicios, Ubicación, Ética y sostenibilidad, Check-in y Check-out, Comodidad y descanso, Oferta gastronómica, Facilidad de reserva y accesibilidad digital, Animación y actividades, Seguridad)
7. Keywords: 3-5 términos relevantes separados por comas SIN espacios
8. Customer_type: Promotor, Leal, Neutral, Crítico, Oportunista
9. Tourist_type: Turista de ocio, cultural, naturaleza, aventura, compras, espiritual/religioso, gastronómico, deportivo, wellness, solidario/voluntario
10. Group_type: familiar, amigos, pareja, solitario, grupo organizado

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con los valores separados por "|" en el orden exacto listado arriba.
Si no puedes determinar algún campo, usa "unknown".
NO incluyas espacios antes o después de los pipes.

Ejemplo: es|Positivo|0.8|joy|4|femenino|Atención al cliente|excelente,servicio,amable|Promotor|Turista de ocio|pareja
"""

    def analizar_con_llm(self, review_text: str, customer_name: str, max_retries: int = 3) -> Optional[Dict]:
        """Analizar una reseña usando el LLM"""
        prompt = self.crear_prompt_analisis(review_text, customer_name)
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un experto en análisis de reseñas de viajes. Respondes SOLO con los valores separados por |."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        for intento in range(max_retries):
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    if not content.strip():
                        print(f"⚠️ Respuesta vacía de la API para reseña")
                        return None
                    
                    # Limpiar posibles markdown o espacios extra
                    if "```" in content:
                        lines = content.split('\n')
                        for line in lines:
                            if '|' in line and not line.strip().startswith('```'):
                                content = line.strip()
                                break
                    
                    content = content.strip()
                    valores = [v.strip() for v in content.split("|")]
                    
                    # Verificar que tenemos el número correcto de campos
                    if len(valores) != len(CAMPOS_ANALISIS):
                        print(f"⚠️ Respuesta incorrecta: {len(valores)} campos vs {len(CAMPOS_ANALISIS)} esperados")
                        return None
                    
                    # Crear diccionario con los resultados
                    resultado = dict(zip(CAMPOS_ANALISIS, valores))
                    return resultado
                
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** intento
                    print(f"⏳ Rate limit alcanzado, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                else:
                    print(f"❌ Error API: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                print(f"❌ Error en petición: {e}")
                if intento < max_retries - 1:
                    time.sleep(1)
        
        return None

    def procesar_reseñas_batch(self, df: pd.DataFrame, batch_size: int = 10, start_index: int = 0) -> Tuple[List[Dict], List[Dict]]:
        """Procesar las reseñas en lotes"""
        # Filtrar solo reseñas no analizadas
        df_pendientes = df[df['analyzed'] == False].iloc[start_index:]
        
        print(f"🤖 Iniciando análisis de {len(df_pendientes)} reseñas...")
        print(f"   - Modelo: {self.model}")
        print(f"   - Tamaño de lote: {batch_size}")
        
        resultados = []
        errores = []
        
        # Procesar en lotes con barra de progreso
        for i in tqdm(range(0, len(df_pendientes), batch_size), desc="Procesando lotes"):
            batch = df_pendientes.iloc[i:i+batch_size]
            
            for idx, row in batch.iterrows():
                resultado = self.analizar_con_llm(
                    row[self.review_text_col], 
                    row[self.customer_name_col]
                )
                
                if resultado:
                    resultado['index'] = idx
                    resultados.append(resultado)
                else:
                    errores.append({
                        'index': idx,
                        'review_id': row.get('review_id', 'N/A'),
                        'error': 'No se pudo analizar'
                    })
                
                # Pausa entre peticiones
                time.sleep(0.5)
            
            # Pausa entre lotes
            if i + batch_size < len(df_pendientes):
                print(f"✅ Lote completado. Esperando antes del siguiente...")
                time.sleep(2)
        
        return resultados, errores

    def actualizar_dataframe(self, df: pd.DataFrame, resultados: List[Dict]) -> pd.DataFrame:
        """Actualizar el DataFrame con los resultados del análisis"""
        # Inicializar las columnas si no existen
        for campo in CAMPOS_ANALISIS:
            if campo not in df.columns:
                df[campo] = None
        
        # Agregar columna 'analyzed' si no existe
        if 'analyzed' not in df.columns:
            df['analyzed'] = False
        
        # Actualizar con los resultados
        for resultado in resultados:
            idx = resultado['index']
            
            # Actualizar cada campo
            for campo in CAMPOS_ANALISIS:
                if campo in resultado:
                    df.loc[idx, campo] = resultado[campo]
            
            # Marcar como analizado
            df.loc[idx, 'analyzed'] = True
        
        return df

    def guardar_resultados(self, df: pd.DataFrame, filename_base: str = 'trustpilot_analyzed') -> str:
        """Guardar los resultados del análisis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_base}_{timestamp}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Resultados guardados en: {filename}")
        
        # También guardar un backup del último estado
        latest_filename = f"{filename_base}_latest.csv"
        df.to_csv(latest_filename, index=False, encoding='utf-8-sig')
        print(f"💾 Backup guardado en: {latest_filename}")
        
        return filename

    def generar_estadisticas(self, df: pd.DataFrame) -> None:
        """Generar y mostrar estadísticas del análisis"""
        print("\n📈 Estadísticas del análisis:")
        
        total_analizadas = df['analyzed'].sum()
        print(f"   - Total de reseñas analizadas: {total_analizadas}")
        
        if total_analizadas > 0:
            if 'sentiment' in df.columns:
                sentiments = df[df['analyzed'] == True]['sentiment'].value_counts().to_dict()
                print(f"   - Sentimientos: {sentiments}")
            
            if 'main_topic' in df.columns:
                topics = df[df['analyzed'] == True]['main_topic'].value_counts().head(5).to_dict()
                print(f"   - Top 5 temas: {topics}")
            
            if 'tourist_type' in df.columns:
                tourist_types = df[df['analyzed'] == True]['tourist_type'].value_counts().head(3).to_dict()
                print(f"   - Tipos de turista: {tourist_types}")
            
            if 'emotion' in df.columns:
                emotions = df[df['analyzed'] == True]['emotion'].value_counts().to_dict()
                print(f"   - Emociones: {emotions}")

    def analizar(self, csv_path: str, batch_size: int = DEFAULT_BATCH_SIZE, max_reviews: Optional[int] = None) -> Tuple[pd.DataFrame, List[Dict]]:
        """Función principal para analizar las reseñas"""
        # Cargar datos
        df = self.cargar_datos(csv_path)
        
        # Limitar número de reseñas si se especifica
        if max_reviews:
            df = df.head(max_reviews)
            print(f"📊 Limitando análisis a {max_reviews} reseñas")
        
        # Procesar reseñas
        resultados, errores = self.procesar_reseñas_batch(df, batch_size)
        
        # Actualizar DataFrame
        print(f"\n✅ Análisis completado:")
        print(f"   - Reseñas analizadas exitosamente: {len(resultados)}")
        print(f"   - Errores: {len(errores)}")
        
        if errores:
            print("❌ Errores encontrados:")
            for error in errores[:5]:  # Mostrar solo los primeros 5 errores
                print(f"   - {error}")
        
        df_actualizado = self.actualizar_dataframe(df, resultados)
        
        # Guardar resultados
        filename = self.guardar_resultados(df_actualizado)
        
        # Mostrar estadísticas
        self.generar_estadisticas(df_actualizado)
        
        return df_actualizado, errores


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Análisis automatizado de reseñas TrustPilot')
    parser.add_argument('csv_file', help='Archivo CSV con las reseñas a analizar')
    parser.add_argument('--api-key', help='API Key de OpenRouter (o usar variable OPENROUTER_API_KEY)')
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f'Modelo a usar (default: {DEFAULT_MODEL})')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help=f'Tamaño del lote (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--max-reviews', type=int, help='Máximo número de reseñas a analizar (opcional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    # Obtener API key
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: API Key de OpenRouter no encontrada")
        print("Usa --api-key o configura la variable de entorno OPENROUTER_API_KEY")
        sys.exit(1)
    
    # Verificar que existe el archivo CSV
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: El archivo {args.csv_file} no existe")
        sys.exit(1)
    
    print("🚀 Iniciando análisis de reseñas TrustPilot")
    print(f"📄 Archivo: {args.csv_file}")
    print(f"🤖 Modelo: {args.model}")
    
    try:
        # Crear analizador
        analyzer = TrustPilotAnalyzer(api_key, args.model)
        
        # Ejecutar análisis
        df_resultado, errores = analyzer.analizar(
            csv_path=args.csv_file,
            batch_size=args.batch_size,
            max_reviews=args.max_reviews
        )
        
        print(f"\n🎉 Análisis completado exitosamente!")
        print(f"📊 Total de reseñas procesadas: {df_resultado['analyzed'].sum()}")
        
        if errores:
            print(f"⚠️ Se encontraron {len(errores)} errores durante el proceso")
            
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 