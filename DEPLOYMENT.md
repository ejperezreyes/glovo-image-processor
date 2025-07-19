# 🚀 Guía de Deployment - Glovo Image Processor

## 🎯 Decisión Final: **NO Firebase, SÍ Railway/Cloud Run**

### ❌ Por qué NO Firebase Functions:
- Límite de 9 minutos (scraping puede tardar más)
- Cold starts problemáticos para webhooks
- Firestore no ideal para nuestras queries relacionales
- Costos impredecibles con volumen

### ✅ Opciones Recomendadas (de más simple a más escalable):

## 🥇 Opción 1: Railway (RECOMENDADO para MVP)

### **Ventajas**:
- ⚡ Deploy en 2 minutos
- 🆓 $5/mes todo incluido
- 🐘 PostgreSQL automático
- 🔄 Auto-deploy desde Git
- 📊 Monitoring incluido

### **Pasos**:

```bash
# 1. Preparar repo
git init
git add .
git commit -m "Initial commit"

# 2. Ir a railway.app
# 3. "Deploy from GitHub repo"
# 4. Seleccionar este repo
# 5. Railway detecta Python automáticamente
# 6. Añadir PostgreSQL service
# 7. ¡Deploy automático!
```

### **Configuración automática**:
```bash
# Railway provee automáticamente:
DATABASE_URL=postgresql://...
PORT=443
RAILWAY_ENVIRONMENT=production

# Variables opcionales a añadir:
SECRET_KEY=tu-clave-secreta-segura
N8N_WEBHOOK_BASE=https://tu-n8n-instance.com
PRICE_PER_IMAGE=0.50
```

---

## 🥈 Opción 2: Google Cloud Run (ESCALABILIDAD)

### **Ventajas**:
- 🌍 Escalabilidad infinita
- 💰 Pay-per-request
- 🚀 0 cold starts con min instances
- 🔐 Integración con Firebase Auth

### **Pasos**:

```bash
# 1. Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash

# 2. Login y configurar proyecto
gcloud auth login
gcloud config set project tu-proyecto-id

# 3. Build y deploy
gcloud run deploy glovo-processor \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300s \
  --min-instances 1

# 4. Configurar Cloud SQL PostgreSQL
gcloud sql instances create glovo-db \
  --database-version POSTGRES_13 \
  --tier db-f1-micro \
  --region europe-west1

# 5. Conectar Cloud Run a Cloud SQL
gcloud run services update glovo-processor \
  --add-cloudsql-instances tu-proyecto:europe-west1:glovo-db
```

### **Variables de entorno**:
```bash
gcloud run services update glovo-processor \
  --set-env-vars DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/instance
```

---

## 🥉 Opción 3: DigitalOcean App Platform (CONTROL TOTAL)

### **Ventajas**:
- 💰 $5/mes droplet + $7/mes managed DB
- 🔧 Control total del stack
- 🌊 Loadbalancer incluido
- 📍 Servidores en Europa

### **Pasos**:

```bash
# 1. Crear cuenta en DigitalOcean
# 2. "Create App" desde GitHub
# 3. Configurar:
#    - Runtime: Python
#    - Build Command: pip install -r requirements.txt
#    - Run Command: gunicorn api_example:app --host 0.0.0.0 --port $PORT
# 4. Añadir PostgreSQL database
# 5. Deploy
```

---

## 🏗️ Opción 4: Docker en cualquier VPS

### **Para máximo control**:

```bash
# 1. En tu VPS (Ubuntu 20.04+)
sudo apt update
sudo apt install docker.io docker-compose

# 2. Clonar repo
git clone https://github.com/tu-usuario/glovo-scrapper
cd glovo-scrapper

# 3. Crear docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/glovo
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=glovo
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# 4. Deploy
docker-compose up -d

# 5. Configurar nginx reverse proxy
sudo apt install nginx
sudo systemctl enable nginx
```

---

## 🎯 MI RECOMENDACIÓN ESPECÍFICA PARA TI

### **Para los próximos 2-3 meses (MVP/Validación)**:

```bash
# USAR: Railway
- Deploy time: 2 minutos
- Costo: $5/mes
- Zero config
- PostgreSQL incluido
- SSL automático
- Monitoring básico

# PASOS EXACTOS:
1. git init && git add . && git commit -m "Deploy ready"
2. Push a GitHub
3. railway.app → "Deploy from GitHub" 
4. Seleccionar repo
5. Add PostgreSQL addon
6. ¡Listo!
```

### **Para escalar (6+ meses)**:

```bash
# MIGRAR A: Google Cloud Run + Cloud SQL
- Frontend: Firebase Hosting (gratis)
- API: Cloud Run (escalabilidad infinita) 
- DB: Cloud SQL (managed PostgreSQL)
- Storage: Firebase Storage
- Auth: Firebase Auth
- CDN: Cloud CDN

# Costo estimado: $20-50/mes con 1000+ restaurants
```

---

## 📊 Comparación de Costos (1000 requests/día)

| Plataforma | Costo Mensual | Setup Time | Escalabilidad |
|------------|---------------|------------|---------------|
| **Railway** | $5-10 | 2 min | Buena |
| **Cloud Run** | $15-25 | 30 min | Excelente |
| **DigitalOcean** | $12-20 | 60 min | Manual |
| **Firebase** | $30-60+ | 45 min | Excelente |

---

## 🚨 IMPORTANTE: Configuración Producción

### **1. Variables de entorno obligatorias**:
```bash
SECRET_KEY=tu-clave-super-secreta-256-bits
DATABASE_URL=postgresql://...
N8N_WEBHOOK_BASE=https://tu-n8n.com
FLASK_ENV=production
```

### **2. Rate limiting**:
```python
# Ya incluido en el código
RATE_LIMIT_PER_MINUTE=10  # Ajustar según necesidades
```

### **3. SSL/HTTPS**:
- Railway: Automático
- Cloud Run: Automático  
- DO/VPS: Usar Cloudflare (gratis)

### **4. Backup base de datos**:
```bash
# Railway: Automático
# Cloud SQL: Automático
# VPS: Configurar manualmente
```

---

## 🎉 Resultado Final

Con **Railway**, en **2 minutos** tendrás:

✅ API funcionando en `https://tu-app.railway.app`  
✅ PostgreSQL configurado automáticamente  
✅ SSL/HTTPS habilitado  
✅ Auto-deploy desde Git  
✅ Monitoring básico  
✅ Logs en tiempo real  

**Costo total: $5/mes** 

### **URLs de ejemplo**:
```
Frontend: https://tu-app.railway.app/
API: https://tu-app.railway.app/api/process-restaurant
Health: https://tu-app.railway.app/health
n8n: https://tu-app.railway.app/api/n8n/pending-jobs
```

**¿Listo para deploy?** 🚀 