import requests
import re
import json
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
from bs4 import BeautifulSoup

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("glovo-improved-scraper")

@dataclass
class ProductInfo:
    """Estructura de datos para productos"""
    id: int
    external_id: str
    store_product_id: str
    name: str
    description: str
    price: float
    price_display: str
    category: str
    category_id: str
    image_url: Optional[str]
    image_id: Optional[str]
    has_promotions: bool
    promotion_discount: Optional[float]
    restaurant_url: str
    restaurant_name: str
    scraped_at: datetime

class GlovoScraperImproved:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Cookie': 'glovo_user_lang=en; glv_device_uid=e8ca3a9b-6f21-47a9-a4d2-03e89a6b1b33'
        })
        
    def extract_product_data(self, restaurant_url: str) -> List[ProductInfo]:
        """Extrae datos de productos de un restaurante usando requests"""
        try:
            log.info(f"🌐 Obteniendo datos de: {restaurant_url}")
            
            response = self.session.get(restaurant_url)
            response.raise_for_status()
            
            # Parse HTML con BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer información del restaurante
            restaurant_name = self._extract_restaurant_name(soup)
            log.info(f"🏪 Restaurante: {restaurant_name}")
            
            # Extraer productos desde HTML
            products = self._extract_products_from_html(soup, restaurant_url, restaurant_name)
            
            log.info(f"✅ Extraídos {len(products)} productos")
            log.info(f"🖼️ Productos con imágenes: {sum(1 for p in products if p.image_url)}")
            log.info(f"📝 Productos sin imágenes: {sum(1 for p in products if not p.image_url)}")
            
            return products
            
        except Exception as e:
            log.error(f"❌ Error procesando {restaurant_url}: {e}")
            return []
    
    def _extract_restaurant_name(self, soup: BeautifulSoup) -> str:
        """Extrae el nombre del restaurante del HTML"""
        try:
            # Buscar en el título de la página
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Extraer nombre antes de "delivery" o "a domicilio"
                for separator in [" delivery", " a domicilio"]:
                    if separator in title_text:
                        return title_text.split(separator)[0].strip()
            
            # Buscar en meta tags
            meta_title = soup.find('meta', {'name': 'title'})
            if meta_title and hasattr(meta_title, 'get') and meta_title.get('content'):
                content = meta_title.get('content', '')
                for separator in [" delivery", " a domicilio"]:
                    if separator in content:
                        return content.split(separator)[0].strip()
            
            return "Unknown Restaurant"
            
        except Exception as e:
            log.warning(f"Error extrayendo nombre del restaurante: {e}")
            return "Unknown Restaurant"
    
    def _extract_products_from_html(self, soup: BeautifulSoup, restaurant_url: str, restaurant_name: str) -> List[ProductInfo]:
        """Extrae productos desde el HTML renderizado"""
        products = []
        
        try:
            # Buscar todos los elementos de productos
            product_rows = soup.find_all(attrs={'data-test-id': 'product-row-content'})
            log.info(f"📦 Encontrados {len(product_rows)} elementos de productos")
            
            current_category = "Unknown Category"
            
            for idx, product_row in enumerate(product_rows):
                try:
                    # Extraer nombre del producto
                    name_element = product_row.find(attrs={'data-test-id': 'product-row-name__highlighter'})
                    if not name_element:
                        continue
                    
                    name = name_element.get_text(strip=True)
                    if not name:
                        continue
                    
                    # Extraer descripción
                    desc_element = product_row.find(attrs={'data-test-id': 'product-row-description__highlighter'})
                    description = desc_element.get_text(strip=True) if desc_element else ""
                    
                    # Extraer precio
                    price_element = product_row.find(attrs={'data-test-id': 'product-row-price'})
                    price_display = price_element.get_text(strip=True) if price_element else ""
                    price = self._parse_price(price_display)
                    
                    # Extraer imagen
                    image_url = None
                    img_element = product_row.find('img', {'data-test-id': 'img-formats'})
                    if img_element and img_element.get('src'):
                        image_url = img_element['src']
                        # Convertir a URL de alta calidad si es de Cloudinary
                        if 'cloudinary.com' in image_url:
                            image_url = self._improve_image_url(image_url)
                    
                    # Detectar promociones
                    promotion_element = product_row.find(attrs={'data-test-id': 'product-row-promotion'})
                    has_promotions = promotion_element is not None
                    promotion_discount = None
                    
                    if has_promotions:
                        promotion_text = promotion_element.get_text(strip=True)
                        discount_match = re.search(r'-(\d+)%', promotion_text)
                        if discount_match:
                            promotion_discount = int(discount_match.group(1))
                    
                    # Crear producto
                    product = ProductInfo(
                        id=idx + 1,  # ID secuencial
                        external_id=f"html_{idx}",
                        store_product_id=f"store_{idx}",
                        name=name,
                        description=description,
                        price=price,
                        price_display=price_display,
                        category=current_category,
                        category_id=self._slugify(current_category),
                        image_url=image_url,
                        image_id=self._extract_image_id(image_url),
                        has_promotions=has_promotions,
                        promotion_discount=promotion_discount,
                        restaurant_url=restaurant_url,
                        restaurant_name=restaurant_name,
                        scraped_at=datetime.now()
                    )
                    
                    products.append(product)
                    
                except Exception as e:
                    log.warning(f"⚠️ Error procesando producto {idx}: {e}")
                    continue
        
        except Exception as e:
            log.error(f"Error extrayendo productos del HTML: {e}")
        
        return products
    
    def _parse_price(self, price_text: str) -> float:
        """Extrae el precio numérico del texto"""
        try:
            # Buscar números con comas decimales
            price_match = re.search(r'(\d+,\d+|\d+\.\d+|\d+)', price_text.replace('€', '').replace(',', '.'))
            if price_match:
                return float(price_match.group(1))
            return 0.0
        except:
            return 0.0
    
    def _improve_image_url(self, image_url: str) -> str:
        """Mejora la calidad de las URLs de Cloudinary"""
        try:
            if 'cloudinary.com' in image_url:
                # Reemplazar parámetros de baja calidad con alta calidad
                improved_url = re.sub(r'q_auto[^,]*', 'q_auto:best', image_url)
                improved_url = re.sub(r'w_\d+', 'w_800', improved_url)
                improved_url = re.sub(r'h_\d+', 'h_800', improved_url)
                return improved_url
            return image_url
        except:
            return image_url
    
    def _extract_image_id(self, image_url: Optional[str]) -> Optional[str]:
        """Extrae el ID de la imagen de la URL"""
        if not image_url:
            return None
        try:
            # Extraer ID de URLs de Cloudinary
            match = re.search(r'/([a-f0-9-]{36})\.', image_url)
            if match:
                return match.group(1)
            return None
        except:
            return None
    
    def _slugify(self, text: str) -> str:
        """Convierte texto a slug"""
        return re.sub(r'[^a-zA-Z0-9]+', '-', text.lower()).strip('-')
    
    def save_to_database(self, products: List[ProductInfo], db_path: str = "glovo_products.db"):
        """Guarda los productos en una base de datos SQLite"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    external_id TEXT,
                    store_product_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL,
                    price_display TEXT,
                    category TEXT,
                    category_id TEXT,
                    image_url TEXT,
                    image_id TEXT,
                    has_promotions BOOLEAN,
                    promotion_discount REAL,
                    restaurant_url TEXT,
                    restaurant_name TEXT,
                    scraped_at TIMESTAMP,
                    url_hash TEXT UNIQUE
                )
            ''')
            
            # Crear tabla para restaurantes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS restaurants (
                    url TEXT PRIMARY KEY,
                    name TEXT,
                    last_scraped TIMESTAMP,
                    total_products INTEGER,
                    products_with_images INTEGER
                )
            ''')
            
            # Insertar productos
            for product in products:
                # Crear hash único para evitar duplicados
                url_hash = hashlib.md5(f"{product.restaurant_url}_{product.name}_{product.price}".encode()).hexdigest()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO products (
                        id, external_id, store_product_id, name, description, price,
                        price_display, category, category_id, image_url, image_id,
                        has_promotions, promotion_discount, restaurant_url, restaurant_name,
                        scraped_at, url_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.id, product.external_id, product.store_product_id,
                    product.name, product.description, product.price,
                    product.price_display, product.category, product.category_id,
                    product.image_url, product.image_id, product.has_promotions,
                    product.promotion_discount, product.restaurant_url, product.restaurant_name,
                    product.scraped_at, url_hash
                ))
            
            # Actualizar tabla de restaurantes
            if products:
                restaurant_url = products[0].restaurant_url
                restaurant_name = products[0].restaurant_name
                total_products = len(products)
                products_with_images = sum(1 for p in products if p.image_url)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO restaurants (
                        url, name, last_scraped, total_products, products_with_images
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (restaurant_url, restaurant_name, datetime.now(), total_products, products_with_images))
            
            conn.commit()
            conn.close()
            
            log.info(f"💾 Guardados {len(products)} productos en la base de datos")
            
        except Exception as e:
            log.error(f"❌ Error guardando en base de datos: {e}")
    
    def get_stats_from_database(self, db_path: str = "glovo_products.db") -> Dict:
        """Obtiene estadísticas de la base de datos"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM products WHERE image_url IS NOT NULL")
            products_with_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT restaurant_url) FROM products")
            total_restaurants = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT category) FROM products")
            total_categories = cursor.fetchone()[0]
            
            # Productos por categoría
            cursor.execute('''
                SELECT category, COUNT(*) 
                FROM products 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            ''')
            products_by_category = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_products': total_products,
                'products_with_images': products_with_images,
                'products_without_images': total_products - products_with_images,
                'total_restaurants': total_restaurants,
                'total_categories': total_categories,
                'products_by_category': products_by_category
            }
            
        except Exception as e:
            log.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}

def main():
    """Función principal para pruebas"""
    scraper = GlovoScraperImproved()
    
    # URL de ejemplo
    restaurant_url = "https://glovoapp.com/es/en/fuengirola/la-pizza-nostra-fuengirola/"
    
    # Extraer productos
    products = scraper.extract_product_data(restaurant_url)
    
    if products:
        # Mostrar algunos productos de ejemplo
        print("\n🍕 PRODUCTOS ENCONTRADOS:")
        for i, product in enumerate(products[:5]):
            print(f"{i+1}. {product.name}")
            print(f"   Precio: {product.price_display}")
            print(f"   Descripción: {product.description[:50]}...")
            print(f"   Imagen: {'✅' if product.image_url else '❌'}")
            if product.has_promotions:
                print(f"   Promoción: -{product.promotion_discount}%")
            print()
        
        # Guardar en base de datos
        scraper.save_to_database(products)
        
        # Mostrar estadísticas
        stats = scraper.get_stats_from_database()
        print("📊 ESTADÍSTICAS:")
        print(f"Total productos: {stats.get('total_products', 0)}")
        print(f"Con imágenes: {stats.get('products_with_images', 0)}")
        print(f"Sin imágenes: {stats.get('products_without_images', 0)}")
        print(f"Restaurantes: {stats.get('total_restaurants', 0)}")
        print(f"Categorías: {stats.get('total_categories', 0)}")
    
    return products

if __name__ == "__main__":
    main() 