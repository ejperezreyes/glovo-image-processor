"""
API Example para el sistema de procesamiento de imágenes de Glovo

Este es un ejemplo simple de cómo crear una API que:
1. Recibe solicitudes de URLs de restaurantes desde el frontend
2. Procesa las imágenes usando el sistema desarrollado
3. Se integra con n8n para el procesamiento de imágenes
4. Proporciona webhooks para recibir resultados de n8n
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
from glovo_business_logic import GlovoImageProcessor

app = Flask(__name__)
processor = GlovoImageProcessor()

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
        return jsonify({"error": str(e)}), 500

@app.route('/api/request-status/<request_id>', methods=['GET'])
def get_request_status(request_id):
    """
    Obtiene el estado de una solicitud de procesamiento
    """
    try:
        status = processor.get_request_status(request_id)
        
        if "error" in status:
            return jsonify(status), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/n8n/pending-jobs', methods=['GET'])
def get_pending_jobs():
    """
    Endpoint para n8n para obtener trabajos pendientes
    
    Query params:
    - limit: número máximo de trabajos (default: 10)
    """
    try:
        limit = int(request.args.get('limit', 10))
        jobs = processor.get_pending_jobs_for_n8n(limit)
        
        return jsonify({
            "success": True,
            "total_jobs": len(jobs),
            "jobs": jobs
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/n8n/start-job/<job_id>', methods=['POST'])
def start_job(job_id):
    """
    Marca un trabajo como iniciado (llamado por n8n)
    
    Body: {
        "webhook_url": "https://n8n.example.com/webhook/job-complete/..."
    }
    """
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return jsonify({"error": "webhook_url requerido"}), 400
        
        processor.mark_job_processing(job_id, webhook_url)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "processing"
        }), 200
        
    except Exception as e:
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
            return jsonify({"error": "Trabajo falló"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<request_id>', methods=['GET'])
def generate_download(request_id):
    """
    Genera un paquete de descarga para el usuario
    
    Query params:
    - type: "watermarked" | "premium"
    """
    try:
        download_type = request.args.get('type', 'watermarked')
        include_watermarked = download_type == 'watermarked'
        
        result = processor.generate_download_package(request_id, include_watermarked)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/payment/process', methods=['POST'])
def process_payment():
    """
    Simula el procesamiento de pagos para remover marcas de agua
    
    Body: {
        "request_id": "...",
        "payment_method": "card",
        "amount": 50.00
    }
    """
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        amount = data.get('amount', 0)
        
        # Aquí irían las integraciones con Stripe, PayPal, etc.
        # Por ahora simulamos un pago exitoso
        
        # Actualizar estado de pago en BD
        # (implementar método en GlovoImageProcessor)
        
        return jsonify({
            "success": True,
            "request_id": request_id,
            "payment_status": "completed",
            "amount_paid": amount,
            "transaction_id": f"txn_{request_id}_{int(datetime.now().timestamp())}"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "glovo-image-processor"
    }), 200

@app.route('/', methods=['GET'])
def frontend_example():
    """
    Ejemplo simple de frontend
    """
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Glovo Image Processor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            input, button { padding: 10px; margin: 10px 0; width: 100%; }
            .result { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
            .loading { color: #666; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍕 Glovo Image Processor</h1>
            <p>Mejora las imágenes de productos de restaurantes de Glovo usando IA</p>
            
            <div>
                <input type="url" id="restaurantUrl" placeholder="URL del restaurante en Glovo" 
                       value="https://glovoapp.com/es/en/fuengirola/la-pizza-nostra-fuengirola/">
                <input type="email" id="userEmail" placeholder="Tu email" value="test@example.com">
                <button onclick="processRestaurant()">🚀 Procesar Restaurante</button>
            </div>
            
            <div id="result" class="result" style="display:none;"></div>
            
            <div id="status" style="display:none;">
                <h3>Estado del Procesamiento</h3>
                <div id="statusContent"></div>
                <button onclick="checkStatus()">🔄 Actualizar Estado</button>
            </div>
        </div>
        
        <script>
            let currentRequestId = null;
            
            async function processRestaurant() {
                const url = document.getElementById('restaurantUrl').value;
                const email = document.getElementById('userEmail').value;
                
                if (!url || !email) {
                    alert('Por favor completa todos los campos');
                    return;
                }
                
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').innerHTML = '<div class="loading">🔄 Procesando solicitud...</div>';
                
                try {
                    const response = await fetch('/api/process-restaurant', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ restaurant_url: url, user_email: email })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        currentRequestId = data.request_id;
                        document.getElementById('result').innerHTML = `
                            <div class="success">
                                <h3>✅ Solicitud Creada Exitosamente</h3>
                                <p><strong>Request ID:</strong> ${data.request_id}</p>
                                <p><strong>Restaurante:</strong> ${data.restaurant_name}</p>
                                <p><strong>Productos:</strong> ${data.total_products}</p>
                                <p><strong>Imágenes a procesar:</strong> ${data.images_to_process}</p>
                                <p><strong>Costo estimado:</strong> €${data.estimated_cost}</p>
                                <p><strong>Tiempo estimado:</strong> ${data.processing_time_minutes} minutos</p>
                            </div>
                        `;
                        document.getElementById('status').style.display = 'block';
                        checkStatus();
                    } else {
                        document.getElementById('result').innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `<div class="error">❌ Error de conexión: ${error.message}</div>`;
                }
            }
            
            async function checkStatus() {
                if (!currentRequestId) return;
                
                try {
                    const response = await fetch(`/api/request-status/${currentRequestId}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        document.getElementById('statusContent').innerHTML = `<div class="error">❌ ${data.error}</div>`;
                        return;
                    }
                    
                    document.getElementById('statusContent').innerHTML = `
                        <p><strong>Progreso:</strong> ${data.progress_percentage}%</p>
                        <p><strong>Estado de trabajos:</strong> ${JSON.stringify(data.job_status)}</p>
                        <p><strong>Imágenes completadas:</strong> ${data.completed_images.length}</p>
                        ${data.progress_percentage === 100 ? 
                            '<button onclick="downloadImages()">📥 Descargar Imágenes (con marca de agua)</button>' : 
                            '<div class="loading">⏳ Procesando...</div>'
                        }
                    `;
                } catch (error) {
                    document.getElementById('statusContent').innerHTML = `<div class="error">❌ Error verificando estado: ${error.message}</div>`;
                }
            }
            
            async function downloadImages() {
                window.open(`/api/download/${currentRequestId}?type=watermarked`, '_blank');
            }
            
            // Auto-refresh cada 30 segundos si hay una solicitud activa
            setInterval(() => {
                if (currentRequestId) checkStatus();
            }, 30000);
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 Iniciando API del procesador de imágenes de Glovo")
    print("📱 Frontend disponible en: http://localhost:5000")
    print("🔗 API endpoints:")
    print("   POST /api/process-restaurant")
    print("   GET  /api/request-status/<request_id>")
    print("   GET  /api/n8n/pending-jobs")
    print("   POST /api/n8n/start-job/<job_id>")
    print("   POST /api/webhook/job-complete/<job_id>")
    print("   GET  /api/download/<request_id>")
    print("   POST /api/payment/process")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 