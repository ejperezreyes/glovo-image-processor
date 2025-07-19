import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from glovo_scraper_improved import GlovoScraperImproved

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("glovo-business")

@dataclass
class ImageProcessingJob:
    """Trabajo de procesamiento de imagen"""
    id: str
    restaurant_url: str
    restaurant_name: str
    product_name: str
    original_image_url: str
    status: str  # pending, processing, completed, failed
    created_at: datetime
    updated_at: datetime
    processed_image_url: Optional[str] = None
    watermarked_image_url: Optional[str] = None
    n8n_webhook_url: Optional[str] = None

@dataclass
class ProcessingRequest:
    """Request de procesamiento de imágenes"""
    restaurant_url: str
    user_email: str
    request_id: str
    payment_status: str  # pending, completed
    watermark_removal_paid: bool = False

class GlovoImageProcessor:
    def __init__(self, db_path: str = "glovo_products.db"):
        self.db_path = db_path
        self.scraper = GlovoScraperImproved()
        self._init_database()
    
    def _init_database(self):
        """Inicializa las tablas adicionales para el procesamiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla para trabajos de procesamiento de imágenes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_processing_jobs (
                    id TEXT PRIMARY KEY,
                    restaurant_url TEXT NOT NULL,
                    restaurant_name TEXT,
                    product_name TEXT,
                    original_image_url TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    processed_image_url TEXT,
                    watermarked_image_url TEXT,
                    n8n_webhook_url TEXT
                )
            ''')
            
            # Tabla para requests de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_requests (
                    request_id TEXT PRIMARY KEY,
                    restaurant_url TEXT NOT NULL,
                    user_email TEXT,
                    payment_status TEXT DEFAULT 'pending',
                    watermark_removal_paid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP,
                    total_images INTEGER,
                    processed_images INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            log.info("✅ Base de datos inicializada")
            
        except Exception as e:
            log.error(f"❌ Error inicializando base de datos: {e}")
    
    def process_restaurant_request(self, restaurant_url: str, user_email: str) -> Dict:
        """Procesa una solicitud de restaurante del usuario"""
        try:
            request_id = hashlib.md5(f"{restaurant_url}_{user_email}_{datetime.now()}".encode()).hexdigest()[:16]
            
            # 1. Verificar si el restaurante ya está en la BD
            existing_data = self._check_existing_restaurant(restaurant_url)
            
            if existing_data:
                log.info(f"🏪 Restaurante ya existe en BD: {existing_data['name']}")
                log.info(f"📊 Productos: {existing_data['total_products']}, Con imágenes: {existing_data['products_with_images']}")
                
                # Verificar si necesita actualización (más de 24 horas)
                if self._needs_update(existing_data['last_scraped']):
                    log.info("🔄 Datos obsoletos, actualizando...")
                    products = self.scraper.extract_product_data(restaurant_url)
                    if products:
                        self.scraper.save_to_database(products)
                        existing_data = self._check_existing_restaurant(restaurant_url)
            else:
                log.info("🆕 Restaurante nuevo, extrayendo datos...")
                products = self.scraper.extract_product_data(restaurant_url)
                if products:
                    self.scraper.save_to_database(products)
                    existing_data = self._check_existing_restaurant(restaurant_url)
                else:
                    return {"error": "No se pudieron extraer datos del restaurante"}
            
            # 2. Crear trabajos de procesamiento para imágenes
            image_jobs = self._create_image_processing_jobs(restaurant_url, request_id)
            
            # 3. Registrar la solicitud del usuario
            self._register_user_request(request_id, restaurant_url, user_email, len(image_jobs))
            
            if not existing_data:
                return {"error": "No se pudieron obtener datos del restaurante"}
            
            return {
                "success": True,
                "request_id": request_id,
                "restaurant_name": existing_data['name'],
                "total_products": existing_data['total_products'],
                "images_to_process": len(image_jobs),
                "estimated_cost": len(image_jobs) * 0.50,  # Ejemplo: €0.50 por imagen
                "processing_time_minutes": len(image_jobs) * 2,  # Ejemplo: 2 min por imagen
            }
            
        except Exception as e:
            log.error(f"❌ Error procesando solicitud: {e}")
            return {"error": str(e)}
    
    def _check_existing_restaurant(self, restaurant_url: str) -> Optional[Dict]:
        """Verifica si el restaurante ya existe en la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT url, name, last_scraped, total_products, products_with_images
                FROM restaurants 
                WHERE url = ?
            ''', (restaurant_url,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'url': result[0],
                    'name': result[1],
                    'last_scraped': result[2],
                    'total_products': result[3],
                    'products_with_images': result[4]
                }
            return None
            
        except Exception as e:
            log.error(f"Error verificando restaurante existente: {e}")
            return None
    
    def _needs_update(self, last_scraped: str) -> bool:
        """Verifica si los datos necesitan actualización"""
        try:
            last_update = datetime.fromisoformat(last_scraped.replace('Z', '+00:00'))
            time_diff = datetime.now() - last_update.replace(tzinfo=None)
            return time_diff > timedelta(hours=24)
        except:
            return True
    
    def _create_image_processing_jobs(self, restaurant_url: str, request_id: str) -> List[ImageProcessingJob]:
        """Crea trabajos de procesamiento para todas las imágenes del restaurante"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener productos con imágenes
            cursor.execute('''
                SELECT name, image_url, restaurant_name
                FROM products 
                WHERE restaurant_url = ? AND image_url IS NOT NULL
            ''', (restaurant_url,))
            
            products_with_images = cursor.fetchall()
            conn.close()
            
            jobs = []
            for product_name, image_url, restaurant_name in products_with_images:
                job_id = hashlib.md5(f"{request_id}_{product_name}_{image_url}".encode()).hexdigest()[:12]
                
                job = ImageProcessingJob(
                    id=job_id,
                    restaurant_url=restaurant_url,
                    restaurant_name=restaurant_name,
                    product_name=product_name,
                    original_image_url=image_url,
                    status='pending',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                jobs.append(job)
                
                # Guardar en BD
                self._save_image_job(job)
            
            log.info(f"📷 Creados {len(jobs)} trabajos de procesamiento de imágenes")
            return jobs
            
        except Exception as e:
            log.error(f"Error creando trabajos de procesamiento: {e}")
            return []
    
    def _save_image_job(self, job: ImageProcessingJob):
        """Guarda un trabajo de procesamiento en la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO image_processing_jobs (
                    id, restaurant_url, restaurant_name, product_name, original_image_url,
                    status, created_at, updated_at, processed_image_url, watermarked_image_url,
                    n8n_webhook_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.id, job.restaurant_url, job.restaurant_name, job.product_name,
                job.original_image_url, job.status, job.created_at, job.updated_at,
                job.processed_image_url, job.watermarked_image_url, job.n8n_webhook_url
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            log.error(f"Error guardando trabajo de imagen: {e}")
    
    def _register_user_request(self, request_id: str, restaurant_url: str, user_email: str, total_images: int):
        """Registra la solicitud del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processing_requests (
                    request_id, restaurant_url, user_email, created_at, total_images
                ) VALUES (?, ?, ?, ?, ?)
            ''', (request_id, restaurant_url, user_email, datetime.now(), total_images))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            log.error(f"Error registrando solicitud de usuario: {e}")
    
    def get_pending_jobs_for_n8n(self, limit: int = 10) -> List[Dict]:
        """Obtiene trabajos pendientes para enviar a n8n"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, restaurant_name, product_name, original_image_url, created_at
                FROM image_processing_jobs 
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))
            
            jobs = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "job_id": job[0],
                    "restaurant_name": job[1],
                    "product_name": job[2],
                    "image_url": job[3],
                    "created_at": job[4],
                    "webhook_url": f"https://your-domain.com/webhook/job-complete/{job[0]}"
                }
                for job in jobs
            ]
            
        except Exception as e:
            log.error(f"Error obteniendo trabajos pendientes: {e}")
            return []
    
    def mark_job_processing(self, job_id: str, n8n_webhook_url: str):
        """Marca un trabajo como en procesamiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE image_processing_jobs 
                SET status = 'processing', n8n_webhook_url = ?, updated_at = ?
                WHERE id = ?
            ''', (n8n_webhook_url, datetime.now(), job_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            log.error(f"Error marcando trabajo como procesando: {e}")
    
    def complete_job(self, job_id: str, processed_image_url: str, watermarked_image_url: str):
        """Completa un trabajo de procesamiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE image_processing_jobs 
                SET status = 'completed', processed_image_url = ?, watermarked_image_url = ?, updated_at = ?
                WHERE id = ?
            ''', (processed_image_url, watermarked_image_url, datetime.now(), job_id))
            
            conn.commit()
            conn.close()
            
            log.info(f"✅ Trabajo {job_id} completado")
            
        except Exception as e:
            log.error(f"Error completando trabajo: {e}")
    
    def get_request_status(self, request_id: str) -> Dict:
        """Obtiene el estado de una solicitud"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener info de la solicitud
            cursor.execute('''
                SELECT restaurant_url, user_email, payment_status, watermark_removal_paid, 
                       created_at, total_images
                FROM processing_requests 
                WHERE request_id = ?
            ''', (request_id,))
            
            request_info = cursor.fetchone()
            if not request_info:
                return {"error": "Solicitud no encontrada"}
            
            # Obtener estado de los trabajos
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM image_processing_jobs 
                WHERE id LIKE ?
                GROUP BY status
            ''', (f"{request_id}%",))
            
            job_status = dict(cursor.fetchall())
            
            # Obtener imágenes completadas
            cursor.execute('''
                SELECT product_name, processed_image_url, watermarked_image_url
                FROM image_processing_jobs 
                WHERE id LIKE ? AND status = 'completed'
            ''', (f"{request_id}%",))
            
            completed_images = cursor.fetchall()
            conn.close()
            
            return {
                "request_id": request_id,
                "restaurant_url": request_info[0],
                "user_email": request_info[1],
                "payment_status": request_info[2],
                "watermark_removal_paid": request_info[3],
                "created_at": request_info[4],
                "total_images": request_info[5],
                "job_status": job_status,
                "completed_images": [
                    {
                        "product_name": img[0],
                        "processed_url": img[1],
                        "watermarked_url": img[2]
                    }
                    for img in completed_images
                ],
                "progress_percentage": round((job_status.get('completed', 0) / request_info[5]) * 100, 1)
            }
            
        except Exception as e:
            log.error(f"Error obteniendo estado de solicitud: {e}")
            return {"error": str(e)}
    
    def generate_download_package(self, request_id: str, include_watermarked: bool = True) -> Dict:
        """Genera un paquete de descarga para el usuario"""
        try:
            status = self.get_request_status(request_id)
            if "error" in status:
                return status
            
            if status["progress_percentage"] < 100:
                return {"error": "El procesamiento aún no está completo"}
            
            # Verificar pago si se requieren imágenes sin marca de agua
            if not include_watermarked and not status["watermark_removal_paid"]:
                return {"error": "Se requiere pago para imágenes sin marca de agua"}
            
            images = []
            for img in status["completed_images"]:
                image_url = img["watermarked_url"] if include_watermarked else img["processed_url"]
                images.append({
                    "product_name": img["product_name"],
                    "download_url": image_url,
                    "filename": f"{img['product_name'].replace(' ', '_')}.jpg"
                })
            
            return {
                "success": True,
                "request_id": request_id,
                "download_type": "watermarked" if include_watermarked else "premium",
                "total_images": len(images),
                "images": images,
                "zip_download_url": f"https://your-domain.com/download/zip/{request_id}?type={'watermarked' if include_watermarked else 'premium'}"
            }
            
        except Exception as e:
            log.error(f"Error generando paquete de descarga: {e}")
            return {"error": str(e)}

def main():
    """Función de prueba"""
    processor = GlovoImageProcessor()
    
    # Simular una solicitud de usuario
    restaurant_url = "https://glovoapp.com/es/en/fuengirola/la-pizza-nostra-fuengirola/"
    user_email = "test@example.com"
    
    print("🚀 Procesando solicitud de restaurante...")
    result = processor.process_restaurant_request(restaurant_url, user_email)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        request_id = result["request_id"]
        
        # Obtener trabajos pendientes para n8n
        print("\n📋 Trabajos pendientes para n8n:")
        pending_jobs = processor.get_pending_jobs_for_n8n(5)
        for job in pending_jobs:
            print(f"- {job['product_name']}: {job['image_url'][:50]}...")
        
        # Simular completar algunos trabajos
        if pending_jobs:
            job_id = pending_jobs[0]['job_id']
            processor.mark_job_processing(job_id, f"https://n8n.example.com/webhook/{job_id}")
            processor.complete_job(
                job_id, 
                "https://processed-images.example.com/image1.jpg",
                "https://watermarked-images.example.com/image1.jpg"
            )
        
        # Verificar estado
        print(f"\n📊 Estado de la solicitud {request_id}:")
        status = processor.get_request_status(request_id)
        print(json.dumps(status, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main() 