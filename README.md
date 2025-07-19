# 🍕 Sistema de Procesamiento de Imágenes de Glovo

Sistema completo para extraer, procesar y mejorar imágenes de productos de restaurantes de Glovo usando IA.

## 🌟 Características

- ✅ **Scraping eficiente** usando requests + BeautifulSoup (no Selenium)
- ✅ **Base de datos SQLite** para almacenar productos e imágenes
- ✅ **API REST** completa para frontend y integraciones
- ✅ **Integración con n8n** para workflows automatizados
- ✅ **Sistema de pagos** para imágenes premium sin marca de agua
- ✅ **Frontend web** funcional incluido

## 📁 Estructura del Proyecto

```
GlovoScrapping/
├── glovo_scraper_improved.py    # Scraper principal (requests + BeautifulSoup)
├── glovo_business_logic.py      # Lógica de negocio y gestión de trabajos
├── api_example.py              # API REST + Frontend web
├── glovo_products.db           # Base de datos SQLite (generada automáticamente)
├── main.py                     # Script original con Selenium (deprecado)
└── README.md                   # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install requests beautifulsoup4 lxml flask sqlite3
```

### 2. Probar el Scraper

```bash
python3 glovo_scraper_improved.py
```

### 3. Probar la Lógica de Negocio

```bash
python3 glovo_business_logic.py
```

### 4. Ejecutar la API + Frontend

```bash
python3 api_example.py
```

Luego visita: http://localhost:5000

## 🔧 Uso del Sistema

### 1. Extracción de Datos

El scraper extrae automáticamente:
- ✅ Nombres de productos
- ✅ Descripciones
- ✅ Precios (incluyendo promociones)
- ✅ URLs de imágenes de alta calidad
- ✅ Categorías
- ✅ Información del restaurante

### 2. Workflow Completo

1. **Usuario introduce URL** del restaurante en el frontend
2. **Sistema verifica** si el restaurante ya está en BD
3. **Si es nuevo**, extrae todos los productos e imágenes
4. **Crea trabajos** de procesamiento para cada imagen
5. **n8n procesa** las imágenes usando IA (Midjourney/Stable Diffusion)
6. **Sistema recibe** resultados via webhook
7. **Usuario descarga** imágenes procesadas (con/sin marca de agua)

## 🛠️ Integración con n8n

### Configurar Workflow en n8n

1. **HTTP Request Node** para obtener trabajos pendientes:
   ```
   GET http://your-domain.com/api/n8n/pending-jobs?limit=5
   ```

2. **For Each Loop** para procesar cada trabajo:
   - Descargar imagen original
   - Procesar con IA (Midjourney/DALL-E/Stable Diffusion)
   - Añadir marca de agua
   - Subir a almacenamiento (S3/Cloudinary)

3. **HTTP Request Node** para notificar completado:
   ```
   POST http://your-domain.com/api/webhook/job-complete/{{job_id}}
   Body: {
     "processed_image_url": "https://processed-images.com/...",
     "watermarked_image_url": "https://watermarked-images.com/...",
     "status": "completed"
   }
   ```

### Ejemplo de Prompting para IA

```
Mejora esta imagen de comida de restaurante:
- Aumenta la saturación y brillo
- Mejora la nitidez y definición
- Haz que se vea más apetitosa
- Mantén el plato principal como foco
- Estilo: fotografía profesional de comida
- Iluminación: cálida y natural
```

## 🗄️ Estructura de Base de Datos

### Tabla `products`
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    price_display TEXT,
    category TEXT,
    image_url TEXT,
    restaurant_url TEXT,
    restaurant_name TEXT,
    scraped_at TIMESTAMP
);
```

### Tabla `image_processing_jobs`
```sql
CREATE TABLE image_processing_jobs (
    id TEXT PRIMARY KEY,
    restaurant_url TEXT NOT NULL,
    product_name TEXT,
    original_image_url TEXT,
    status TEXT DEFAULT 'pending',
    processed_image_url TEXT,
    watermarked_image_url TEXT,
    created_at TIMESTAMP
);
```

### Tabla `processing_requests`
```sql
CREATE TABLE processing_requests (
    request_id TEXT PRIMARY KEY,
    restaurant_url TEXT NOT NULL,
    user_email TEXT,
    payment_status TEXT DEFAULT 'pending',
    watermark_removal_paid BOOLEAN DEFAULT FALSE,
    total_images INTEGER
);
```

## 🌐 API Endpoints

### Frontend/Usuario

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Frontend web |
| `/api/process-restaurant` | POST | Iniciar procesamiento |
| `/api/request-status/<id>` | GET | Verificar estado |
| `/api/download/<id>` | GET | Descargar imágenes |
| `/api/payment/process` | POST | Procesar pago |

### Integración n8n

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/n8n/pending-jobs` | GET | Obtener trabajos pendientes |
| `/api/n8n/start-job/<id>` | POST | Marcar trabajo como iniciado |
| `/api/webhook/job-complete/<id>` | POST | Notificar trabajo completado |

## 💰 Modelo de Negocio

### Pricing Sugerido
- **Imágenes con marca de agua**: GRATIS
- **Imágenes sin marca de agua**: €0.50 por imagen
- **Paquetes**: Descuentos por volumen
- **Suscripción Premium**: Procesamiento ilimitado

### Métricas de Ejemplo
- **La Pizza Nostra**: 164 productos, 131 imágenes
- **Costo estimado**: €65.50 por restaurante
- **Tiempo de procesamiento**: ~4 horas (2 min/imagen)

## 🔐 Consideraciones de Seguridad

- ✅ Validación de URLs de Glovo
- ✅ Rate limiting para evitar abuse
- ✅ Webhooks seguros con tokens
- ✅ Almacenamiento seguro de imágenes
- ⚠️ Implementar autenticación de usuarios
- ⚠️ Encriptar datos sensibles
- ⚠️ Usar HTTPS en producción

## 🚀 Despliegue en Producción

### Opción 1: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "api_example.py"]
```

### Opción 2: VPS/Cloud
- **DigitalOcean Droplet**: $5-20/mes
- **AWS EC2**: t3.micro-medium
- **Google Cloud Run**: Serverless option
- **Heroku**: Fácil despliegue

### Base de Datos en Producción
- **PostgreSQL**: Para más concurrencia
- **Redis**: Para cache y trabajos
- **S3/Cloudinary**: Para almacenar imágenes

## 📊 Monitoreo y Analytics

```python
# Métricas importantes a trackear
- Restaurantes procesados por día
- Imágenes procesadas por hora
- Tiempo promedio de procesamiento
- Tasa de conversión (free → paid)
- Errores y fallos de procesamiento
```

## 🛡️ Términos Legales

⚠️ **Importante**: Este sistema es para propósitos educativos. Para uso comercial:

1. **Revisar términos de servicio** de Glovo
2. **Contactar con restaurantes** para obtener permisos
3. **Respetar derechos de autor** de las imágenes
4. **Implementar robots.txt compliance**
5. **Considerar aspectos de GDPR/privacidad**

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte y Consultas

Para consultas sobre implementación, integración con n8n, o escalamiento:
- 📧 Email: [tu-email@example.com]
- 💬 Discord: [tu-servidor]
- 🐦 Twitter: [@tu-handle]

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

---

**⚡ Potenciado por**: Python, BeautifulSoup, SQLite, Flask, n8n

**🚀 ¿Listo para revolucionar las imágenes de comida con IA?** 