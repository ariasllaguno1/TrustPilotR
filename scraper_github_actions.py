#!/usr/bin/env python3
"""
TrustPilot Scraper para GitHub Actions
Versión optimizada para ejecutar en modo headless sin interfaz gráfica
"""

import os
import sys
import argparse
import traceback
from datetime import datetime

# Configurar variables de entorno para modo headless
os.environ["DISPLAY"] = ":99"
os.environ["CHROME_BIN"] = "/usr/bin/google-chrome"

# Importar todas las librerías necesarias
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm
import json
import hashlib
import random
import glob

def setup_driver_github_actions(headless=True):
    """Configuración optimizada del driver para GitHub Actions"""
    chrome_options = Options()
    
    # Configuración para GitHub Actions
    if headless:
        chrome_options.add_argument('--headless')
    
    # Opciones obligatorias para CI/CD
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # User agent realista
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    
    # Otras opciones de rendimiento
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Usar Chrome del sistema en GitHub Actions
        chrome_options.binary_location = "/usr/bin/google-chrome"
        service = Service("/usr/bin/chromedriver")
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(10)
        
        print("✅ Driver Chrome iniciado correctamente para GitHub Actions")
        return driver
        
    except Exception as e:
        print(f"❌ Error al iniciar Chrome: {e}")
        # Fallback: intentar con webdriver-manager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Driver Chrome iniciado con webdriver-manager")
            return driver
        except Exception as e2:
            print(f"❌ Error con fallback: {e2}")
            raise e

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para parecer más humano"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def generate_review_id(company_name, review_date, customer_name, review_text):
    """Genera un ID único para cada reseña"""
    content = f"{company_name}{review_date}{customer_name}{review_text[:50]}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def parse_date(date_str):
    """Convierte la fecha del formato de Trustpilot a formato estándar"""
    try:
        # Mapeo de meses en español
        meses = {
            'enero': 'January', 'febrero': 'February', 'marzo': 'March',
            'abril': 'April', 'mayo': 'May', 'junio': 'June',
            'julio': 'July', 'agosto': 'August', 'septiembre': 'September',
            'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December'
        }
        
        # Reemplazar mes español por inglés
        for mes_esp, mes_eng in meses.items():
            date_str = date_str.replace(mes_esp, mes_eng)
        
        # Parsear fecha
        return pd.to_datetime(date_str, format='%d de %B de %Y')
    except:
        return None

def scroll_to_load_reviews(driver, max_scrolls=5):
    """Hace scroll para cargar más reseñas (reducido para GitHub Actions)"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Reducido para GitHub Actions
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
            
        last_height = new_height
        scrolls += 1

def get_companies_from_category(driver, category_url, max_pages=5):
    """Extrae información de empresas de una categoría (optimizado para CI/CD)"""
    companies = []
    
    for page in range(1, max_pages + 1):
        url = f"{category_url}?page={page}"
        print(f"🔍 Página {page}: {url}")
        
        try:
            driver.get(url)
            time.sleep(3)  # Reducido para GitHub Actions
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Buscar enlaces de empresas
            company_links = soup.find_all('a', href=re.compile('/review/[^/?]+$'))
            
            if not company_links:
                print(f"⚠️ No se encontraron empresas en la página {page}")
                continue
            
            print(f"✅ Encontradas {len(company_links)} empresas")
            
            for link in company_links:
                try:
                    company_url = link.get('href', '')
                    if not company_url.startswith('http'):
                        company_url = f"https://es.trustpilot.com{company_url}"
                    
                    domain = company_url.split('/')[-1].split('?')[0]
                    company_name = link.get_text(strip=True) or domain
                    
                    companies.append({
                        'company_name': company_name,
                        'domain': domain,
                        'company_url': company_url,
                        'rating': 'N/A',
                        'num_reviews': '0',
                        'categories': 'travel_vacation'
                    })
                    
                except Exception as e:
                    print(f"Error procesando empresa: {e}")
                    continue
        
        except Exception as e:
            print(f"Error en página {page}: {e}")
            continue
    
    # Eliminar duplicados
    seen = set()
    unique_companies = []
    for company in companies:
        if company['company_url'] not in seen:
            seen.add(company['company_url'])
            unique_companies.append(company)
    
    print(f"✅ Total empresas únicas: {len(unique_companies)}")
    return unique_companies

def get_reviews_from_company(driver, company_info, max_review_pages=3):
    """Extrae reseñas de una empresa (optimizado para GitHub Actions)"""
    reviews = []
    subcategories = ""
    
    for page in range(1, max_review_pages + 1):
        if page == 1:
            review_url = company_info['company_url']
        else:
            review_url = f"{company_info['company_url']}?page={page}"
        
        print(f"   📄 Página {page}: {review_url}")
        
        try:
            driver.get(review_url)
            time.sleep(2)  # Reducido para GitHub Actions
            
            # Extraer subcategorías solo en la primera página
            if page == 1:
                try:
                    soup_page = BeautifulSoup(driver.page_source, 'html.parser')
                    breadcrumb_elem = soup_page.find('nav', attrs={'aria-label': re.compile('breadcrumb', re.I)})
                    
                    if breadcrumb_elem:
                        breadcrumb_links = breadcrumb_elem.find_all('a')
                        subcategory_list = []
                        
                        for link in breadcrumb_links:
                            text = link.text.strip()
                            if text and text.lower() not in ['home', 'inicio', 'trustpilot']:
                                subcategory_list.append(text)
                        
                        subcategories = " > ".join(subcategory_list)
                        print(f"   📁 Subcategorías: {subcategories}")
                except Exception as e:
                    print(f"   ⚠️ Error extrayendo subcategorías: {e}")
            
            # Scroll limitado para GitHub Actions
            scroll_to_load_reviews(driver, max_scrolls=2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            review_cards = soup.find_all('article', class_=re.compile('paper_paper__'))
            
            if not review_cards:
                print(f"   ⚠️ No se encontraron reseñas en página {page}")
                break
            
            page_reviews = 0
            for card in review_cards:
                try:
                    # Nombre del cliente
                    customer_elem = card.find('span', attrs={'data-consumer-name-typography': 'true'})
                    customer_name = customer_elem.text.strip() if customer_elem else "Anónimo"
                    
                    # Fecha de la reseña
                    date_elem = card.find('time')
                    review_date = date_elem.get('datetime', '') if date_elem else ""
                    
                    # Puntuación
                    rating_elem = card.find('div', attrs={'data-service-review-rating': True})
                    if rating_elem:
                        customer_score = int(rating_elem.get('data-service-review-rating', '0'))
                    else:
                        customer_score = 0
                    
                    # Texto de la reseña
                    review_elem = card.find('p', attrs={'data-service-review-text-typography': 'true'})
                    review_text = review_elem.text.strip() if review_elem else ""
                    
                    if review_text:  # Solo guardar si hay texto
                        review_id = generate_review_id(
                            company_info['company_name'], 
                            str(review_date), 
                            customer_name, 
                            review_text
                        )
                        
                        reviews.append({
                            'review_id': review_id,
                            'domain': company_info['domain'],
                            'company_name': company_info['company_name'],
                            'categories': company_info['categories'],
                            'subcategories': subcategories,
                            'company_rating': company_info['rating'],
                            'review_date': review_date,
                            'customer_name': customer_name,
                            'customer_score': customer_score,
                            'review_text': review_text,
                            'language': '',
                            'sentiment': '',
                            'emotion': '',
                            'customer_gender': '',
                            'main_topic': '',
                            'keywords': '',
                            'customer_type': '',
                            'tourist_type': '',
                            'group_type': '',
                            'analyzed': False
                        })
                        page_reviews += 1
                    
                except Exception as e:
                    print(f"   ❌ Error procesando reseña: {e}")
                    continue
            
            print(f"   ✅ Página {page}: {page_reviews} reseñas extraídas")
            
            if page_reviews == 0:
                break
                
        except Exception as e:
            print(f"   ❌ Error en página {page}: {e}")
            break
    
    print(f"📊 Total: {len(reviews)} reseñas de {company_info['company_name']}")
    return reviews

def run_scraper_github_actions(max_companies=100, max_review_pages=10, max_company_pages=10):
    """Función principal optimizada para GitHub Actions"""
    
    print("🤖 Iniciando TrustPilot Scraper para GitHub Actions")
    print(f"📊 Parámetros: {max_companies} empresas, {max_review_pages} páginas/empresa, {max_company_pages} páginas categoría")
    
    # Crear directorio de resultados
    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Inicializar driver
    driver = setup_driver_github_actions(headless=True)
    
    try:
        # URL de la categoría
        category_url = "https://es.trustpilot.com/categories/travel_vacation"
        
        # Obtener empresas
        print("\n🔍 Obteniendo lista de empresas...")
        companies = get_companies_from_category(driver, category_url, max_pages=max_company_pages)
        
        # Limitar número de empresas
        companies = companies[:max_companies]
        print(f"\n📋 Procesando {len(companies)} empresas")
        
        # Procesar empresas
        all_reviews = []
        processed_companies = []
        
        for i, company in enumerate(tqdm(companies, desc="Empresas")):
            print(f"\n[{i+1}/{len(companies)}] 🏢 {company['company_name']}")
            
            try:
                reviews = get_reviews_from_company(driver, company, max_review_pages=max_review_pages)
                
                if reviews:
                    all_reviews.extend(reviews)
                    
                    # Guardar CSV individual
                    df_company = pd.DataFrame(reviews)
                    csv_filename = f"results/reviews_{company['domain']}_{timestamp}.csv"
                    df_company.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"   💾 Guardado: {csv_filename}")
                
                processed_companies.append({
                    'company_name': company['company_name'],
                    'domain': company['domain'],
                    'reviews_count': len(reviews),
                    'processed_at': datetime.now().isoformat()
                })
                
                # Pausa entre empresas (reducida para GitHub Actions)
                if i < len(companies) - 1:
                    random_delay(1, 2)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Crear DataFrame consolidado
        if all_reviews:
            df_consolidated = pd.DataFrame(all_reviews)
            
            # Guardar archivo consolidado
            consolidated_filename = f"trustpilot_consolidated_{timestamp}.csv"
            df_consolidated.to_csv(consolidated_filename, index=False, encoding='utf-8-sig')
            
            # Guardar resumen de empresas procesadas
            df_companies = pd.DataFrame(processed_companies)
            companies_filename = f"companies_processed_{timestamp}.csv"
            df_companies.to_csv(companies_filename, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ SCRAPING COMPLETADO!")
            print(f"📊 Total reseñas: {len(all_reviews):,}")
            print(f"🏢 Empresas procesadas: {len(processed_companies)}")
            print(f"📁 Archivo principal: {consolidated_filename}")
            print(f"📁 Archivo empresas: {companies_filename}")
            
            # Estadísticas
            if len(df_consolidated) > 0:
                print(f"\n📈 Estadísticas:")
                print(f"   • Empresas únicas: {df_consolidated['company_name'].nunique()}")
                print(f"   • Promedio reseñas/empresa: {len(df_consolidated) / df_consolidated['company_name'].nunique():.1f}")
                
                score_dist = df_consolidated['customer_score'].value_counts().sort_index()
                print(f"   • Distribución de puntuaciones:")
                for score, count in score_dist.items():
                    print(f"     ⭐ {score}: {count} ({count/len(df_consolidated)*100:.1f}%)")
            
            return df_consolidated
        else:
            print("⚠️ No se extrajeron reseñas")
            return None
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return None
        
    finally:
        try:
            driver.quit()
            print("\n🔚 Navegador cerrado")
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='TrustPilot Scraper para GitHub Actions')
    parser.add_argument('--max_companies', type=int, default=100, help='Número máximo de empresas')
    parser.add_argument('--max_review_pages', type=int, default=10, help='Páginas de reseñas por empresa')
    parser.add_argument('--max_company_pages', type=int, default=10, help='Páginas de categoría')
    
    args = parser.parse_args()
    
    try:
        result = run_scraper_github_actions(
            max_companies=args.max_companies,
            max_review_pages=args.max_review_pages,
            max_company_pages=args.max_company_pages
        )
        
        if result is not None:
            print("🎉 Ejecución exitosa!")
            sys.exit(0)
        else:
            print("❌ No se obtuvieron resultados")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 