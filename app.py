"""
🚀 Production-ready API para Glovo Image Processor

Versión optimizada para deployment en Railway/Cloud Run
Con soporte para PostgreSQL y configuración por variables de entorno
"""

from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime
from config import Config, get_db_connection, is_production, get_env_info
from glovo_business_logic import GlovoImageProcessor

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize processor with database configuration
if is_production():
    # Production: Use PostgreSQL
    processor = GlovoImageProcessor(db_type='postgresql')
else:
    # Development: Use SQLite
    processor = GlovoImageProcessor(db_type='sqlite')

# Simulación de datos de usuario (en producción usar una BD real)
USERS = {
    "test@example.com": {"credits": 100, "premium": False}
}

@app.route('/api/process-restaurant', methods=['POST'])
def process_restaurant():
    """
    Endpoint principal para procesar un restaurante
    
    Body: {
        "restaurant_url": "https://glovoapp.com/es/en/fuengirola/...",
        "user_email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        restaurant_url = data.get('restaurant_url')
        user_email = data.get('user_email')
        
        if not restaurant_url or not user_email:
            return jsonify({"error": "Faltan parámetros requeridos"}), 400
        
        # Validar URL de Glovo
        if 'glovoapp.com' not in restaurant_url:
            return jsonify({"error": "URL de restaurante inválida"}), 400
        
        # Procesar solicitud
        result = processor.process_restaurant_request(restaurant_url, user_email)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        app.logger.error(f"Error processing restaurant: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/request-status/<request_id>', methods=['GET'])
def get_request_status(request_id):
    """
    Obtener el estado de una solicitud de procesamiento
    """
    try:
        status = processor.get_request_status(request_id)
        
        if not status:
            return jsonify({"error": "Solicitud no encontrada"}), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        app.logger.error(f"Error getting request status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/n8n/pending-jobs', methods=['GET'])
def get_pending_jobs():
    """
    Endpoint para n8n: obtener trabajos pendientes de procesamiento
    
    Query params:
    - limit: número máximo de trabajos (default: 5)
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        jobs = processor.get_pending_jobs_for_n8n(limit)
        
        return jsonify({
            "success": True,
            "jobs": jobs,
            "count": len(jobs)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting pending jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/n8n/start-job/<job_id>', methods=['POST'])
def start_job(job_id):
    """
    Endpoint para n8n: marcar un trabajo como iniciado
    
    Body: {
        "webhook_url": "https://n8n.example.com/webhook/result/job_123"
    }
    """
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url') if data else None
        
        processor.mark_job_processing(job_id, webhook_url)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "processing"
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error starting job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook/job-complete/<job_id>', methods=['POST'])
def job_complete_webhook(job_id):
    """
    Webhook para recibir resultados de n8n cuando completa un trabajo
    
    Body: {
        "processed_image_url": "https://processed-images.com/...",
        "watermarked_image_url": "https://watermarked-images.com/...",
        "status": "completed" | "failed"
    }
    """
    try:
        data = request.get_json()
        
        if data.get('status') == 'completed':
            processed_url = data.get('processed_image_url')
            watermarked_url = data.get('watermarked_image_url')
            
            if not processed_url or not watermarked_url:
                return jsonify({"error": "URLs de imagen requeridas"}), 400
            
            processor.complete_job(job_id, processed_url, watermarked_url)
            
            return jsonify({
                "success": True,
                "job_id": job_id,
                "message": "Trabajo completado exitosamente"
            }), 200
        else:
            # Manejar fallos aquí
            app.logger.warning(f"Job {job_id} failed: {data}")
            return jsonify({"error": "Trabajo falló"}), 400
        
    except Exception as e:
        app.logger.error(f"Error completing job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<request_id>', methods=['GET'])
def download_images(request_id):
    """
    Descargar imágenes procesadas (con o sin marca de agua)
    
    Query params:
    - type: 'watermarked' | 'premium' (default: watermarked)
    """
    try:
        image_type = request.args.get('type', 'watermarked')
        
        # Obtener URLs de imágenes completadas
        images = processor.get_completed_images(request_id, image_type)
        
        if not images:
            return jsonify({"error": "No hay imágenes disponibles"}), 404
        
        return jsonify({
            "success": True,
            "request_id": request_id,
            "image_type": image_type,
            "images": images,
            "download_urls": [img['url'] for img in images]
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error downloading images: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/payment/process', methods=['POST'])
def process_payment():
    """
    Procesar pago para remover marcas de agua
    
    Body: {
        "request_id": "abc123",
        "payment_token": "stripe_token_xyz"
    }
    """
    # TODO: Integrar con Stripe o sistema de pagos real
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        payment_token = data.get('payment_token')
        
        if not request_id or not payment_token:
            return jsonify({"error": "Faltan parámetros de pago"}), 400
        
        # Simular procesamiento de pago exitoso
        # En producción: validar con Stripe, PayPal, etc.
        
        result = processor.process_payment(request_id, payment_token)
        
        return jsonify(result), 200
        
    except Exception as e:
        app.logger.error(f"Error processing payment: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para monitoring"""
    try:
        # Test database connection
        conn = get_db_connection()
        conn.close()
        
        env_info = get_env_info()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "glovo-image-processor",
            "environment": env_info,
            "database": "connected"
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/info', methods=['GET'])
def system_info():
    """System information endpoint"""
    return jsonify({
        "system": "Glovo Image Processor",
        "version": "1.0.0",
        "environment": get_env_info(),
        "endpoints": {
            "frontend": "/",
            "process": "/api/process-restaurant",
            "status": "/api/request-status/<id>",
            "n8n_jobs": "/api/n8n/pending-jobs",
            "webhook": "/api/webhook/job-complete/<id>",
            "download": "/api/download/<id>",
            "health": "/health"
        }
    })

@app.route('/', methods=['GET'])
def frontend():
    """
    Frontend web mejorado para producción
    """
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🍕 Glovo Image Processor</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #ff6b6b, #feca57);
                padding: 40px;
                text-align: center;
                color: white;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 700;
            }
            
            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            
            .content {
                padding: 40px;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            }
            
            input {
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: border-color 0.3s ease;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
                width: 100%;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            
            .result.success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            
            .result.error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            
            .result.loading {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
            }
            
            .status-section {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;
            }
            
            .progress-bar {
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 15px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #ff6b6b, #feca57);
                transition: width 0.5s ease;
                width: 0%;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .stat-value {
                font-size: 2rem;
                font-weight: bold;
                color: #667eea;
            }
            
            .stat-label {
                color: #666;
                margin-top: 5px;
            }
            
            .footer {
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; }
                .header h1 { font-size: 2rem; }
                .content { padding: 20px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍕 Glovo Image Processor</h1>
                <p>Mejora las imágenes de productos de restaurantes usando IA</p>
            </div>
            
            <div class="content">
                <form id="processForm">
                    <div class="form-group">
                        <label for="restaurantUrl">URL del Restaurante en Glovo</label>
                        <input type="url" id="restaurantUrl" placeholder="https://glovoapp.com/es/en/fuengirola/..." 
                               value="https://glovoapp.com/es/en/fuengirola/la-pizza-nostra-fuengirola/" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="userEmail">Tu Email</label>
                        <input type="email" id="userEmail" placeholder="tu@email.com" 
                               value="test@example.com" required>
                    </div>
                    
                    <button type="submit" class="btn" id="submitBtn">
                        🚀 Procesar Restaurante
                    </button>
                </form>
                
                <div id="result" class="result"></div>
                
                <div id="statusSection" class="status-section">
                    <h3>📊 Estado del Procesamiento</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div id="progressText">0% completado</div>
                    
                    <div class="stats" id="stats"></div>
                    
                    <button class="btn" onclick="checkStatus()" id="refreshBtn">
                        🔄 Actualizar Estado
                    </button>
                </div>
            </div>
            
            <div class="footer">
                <p>{{ get_env_info()['environment'].title() }} Environment • 
                   Database: {{ get_env_info()['database_type'].title() }} • 
                   ❤️ Hecho con Flask</p>
            </div>
        </div>
        
        <script>
            let currentRequestId = null;
            let refreshInterval = null;
            
            document.getElementById('processForm').addEventListener('submit', processRestaurant);
            
            async function processRestaurant(e) {
                e.preventDefault();
                
                const url = document.getElementById('restaurantUrl').value;
                const email = document.getElementById('userEmail').value;
                const submitBtn = document.getElementById('submitBtn');
                const result = document.getElementById('result');
                
                // Disable form
                submitBtn.disabled = true;
                submitBtn.textContent = '🔄 Procesando...';
                
                // Show loading
                showResult('loading', '🔄 Analizando restaurante...');
                
                try {
                    const response = await fetch('/api/process-restaurant', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ restaurant_url: url, user_email: email })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        currentRequestId = data.request_id;
                        
                        showResult('success', `
                            <h3>✅ Solicitud Creada Exitosamente</h3>
                            <div class="stats">
                                <div class="stat-card">
                                    <div class="stat-value">${data.total_products}</div>
                                    <div class="stat-label">Productos</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.images_to_process}</div>
                                    <div class="stat-label">Imágenes</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">€${data.estimated_cost}</div>
                                    <div class="stat-label">Costo</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.processing_time_minutes}min</div>
                                    <div class="stat-label">Tiempo</div>
                                </div>
                            </div>
                            <p><strong>Request ID:</strong> ${data.request_id}</p>
                            <p><strong>Restaurante:</strong> ${data.restaurant_name}</p>
                        `);
                        
                        document.getElementById('statusSection').style.display = 'block';
                        startAutoRefresh();
                        checkStatus();
                    } else {
                        showResult('error', `❌ Error: ${data.error}`);
                    }
                } catch (error) {
                    showResult('error', `❌ Error de conexión: ${error.message}`);
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Procesar Restaurante';
                }
            }
            
            async function checkStatus() {
                if (!currentRequestId) return;
                
                try {
                    const response = await fetch(`/api/request-status/${currentRequestId}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        showResult('error', `❌ ${data.error}`);
                        return;
                    }
                    
                    updateProgress(data.progress_percentage);
                    updateStats(data);
                    
                    if (data.progress_percentage === 100) {
                        stopAutoRefresh();
                        showDownloadButton();
                    }
                } catch (error) {
                    console.error('Error checking status:', error);
                }
            }
            
            function updateProgress(percentage) {
                const progressFill = document.getElementById('progressFill');
                const progressText = document.getElementById('progressText');
                
                progressFill.style.width = percentage + '%';
                progressText.textContent = `${percentage}% completado`;
            }
            
            function updateStats(data) {
                const stats = document.getElementById('stats');
                stats.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${data.completed_images.length}</div>
                        <div class="stat-label">Completadas</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${Object.values(data.job_status).filter(s => s === 'pending').length}</div>
                        <div class="stat-label">Pendientes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${Object.values(data.job_status).filter(s => s === 'processing').length}</div>
                        <div class="stat-label">Procesando</div>
                    </div>
                `;
            }
            
            function showDownloadButton() {
                const stats = document.getElementById('stats');
                stats.innerHTML += `
                    <div class="stat-card" style="grid-column: 1/-1;">
                        <button class="btn" onclick="downloadImages()">
                            📥 Descargar Imágenes (con marca de agua)
                        </button>
                    </div>
                `;
            }
            
            function downloadImages() {
                window.open(`/api/download/${currentRequestId}?type=watermarked`, '_blank');
            }
            
            function startAutoRefresh() {
                refreshInterval = setInterval(checkStatus, 10000); // cada 10 segundos
            }
            
            function stopAutoRefresh() {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
            }
            
            function showResult(type, message) {
                const result = document.getElementById('result');
                result.className = `result ${type}`;
                result.innerHTML = message;
                result.style.display = 'block';
            }
        </script>
    </body>
    </html>
    ''', get_env_info=get_env_info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not is_production()
    
    print("🚀 Iniciando Glovo Image Processor API")
    print(f"🌍 Environment: {get_env_info()['environment']}")
    print(f"🗄️ Database: {get_env_info()['database_type']}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📱 Frontend: http://{'0.0.0.0' if is_production() else 'localhost'}:{port}")
    print("🔗 API endpoints:")
    print("   POST /api/process-restaurant")
    print("   GET  /api/request-status/<request_id>")
    print("   GET  /api/n8n/pending-jobs")
    print("   POST /api/n8n/start-job/<job_id>")
    print("   POST /api/webhook/job-complete/<job_id>")
    print("   GET  /api/download/<request_id>")
    print("   POST /api/payment/process")
    print("   GET  /health")
    print("   GET  /info")
    
    app.run(debug=debug, host='0.0.0.0', port=port) 