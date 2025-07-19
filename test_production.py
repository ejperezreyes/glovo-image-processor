#!/usr/bin/env python3
"""
🧪 Script para probar la aplicación en producción

Ejecutar después del deployment para verificar que todo funciona
"""

import requests
import json
import time

# CAMBIAR ESTA URL por tu URL de Railway
BASE_URL = "https://TU-PROYECTO.up.railway.app"

def test_endpoints():
    """Probar todos los endpoints principales"""
    
    print("🧪 Probando aplicación en producción...")
    print(f"🌍 URL base: {BASE_URL}")
    
    # 1. Health check
    print("\n1️⃣ Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK - Environment: {data.get('environment', {}).get('environment')}")
            print(f"   Database: {data.get('environment', {}).get('database_type')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # 2. Info endpoint
    print("\n2️⃣ Probando system info...")
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=10)
        if response.status_code == 200:
            print("✅ System info OK")
        else:
            print(f"❌ System info failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System info error: {e}")
    
    # 3. Frontend
    print("\n3️⃣ Probando frontend...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200 and "Glovo Image Processor" in response.text:
            print("✅ Frontend OK")
        else:
            print(f"❌ Frontend failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend error: {e}")
    
    # 4. Process restaurant endpoint (simulación)
    print("\n4️⃣ Probando API de procesamiento...")
    try:
        test_data = {
            "restaurant_url": "https://glovoapp.com/es/en/fuengirola/la-pizza-nostra-fuengirola/",
            "user_email": "test@example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/process-restaurant",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API procesamiento OK")
                print(f"   Request ID: {data.get('request_id')}")
                print(f"   Restaurante: {data.get('restaurant_name')}")
                print(f"   Productos: {data.get('total_products')}")
                print(f"   Imágenes: {data.get('images_to_process')}")
                return data.get('request_id')
            else:
                print(f"❌ API error: {data.get('error')}")
        else:
            print(f"❌ API failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    return None

def test_status_endpoint(request_id):
    """Probar endpoint de estado"""
    if not request_id:
        return
    
    print(f"\n5️⃣ Probando estado de solicitud {request_id}...")
    try:
        response = requests.get(f"{BASE_URL}/api/request-status/{request_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint OK")
            print(f"   Progreso: {data.get('progress_percentage', 0)}%")
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")

def test_n8n_endpoint():
    """Probar endpoint de n8n"""
    print("\n6️⃣ Probando endpoint n8n...")
    try:
        response = requests.get(f"{BASE_URL}/api/n8n/pending-jobs?limit=3", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ n8n endpoint OK")
            print(f"   Trabajos pendientes: {data.get('count', 0)}")
        else:
            print(f"❌ n8n failed: {response.status_code}")
    except Exception as e:
        print(f"❌ n8n error: {e}")

if __name__ == "__main__":
    print("🚀 TESTING GLOVO IMAGE PROCESSOR IN PRODUCTION")
    print("=" * 60)
    
    if "TU-PROYECTO" in BASE_URL:
        print("⚠️  IMPORTANTE: Cambia la URL BASE_URL en este script")
        print("   Ejemplo: https://glovo-processor-xyz.up.railway.app")
        print("\nEjecutar con:")
        print("python test_production.py")
        exit(1)
    
    # Ejecutar todas las pruebas
    request_id = test_endpoints()
    test_status_endpoint(request_id)
    test_n8n_endpoint()
    
    print("\n" + "=" * 60)
    print("🎉 TESTS COMPLETADOS")
    print("\n📱 URLs para probar manualmente:")
    print(f"Frontend:  {BASE_URL}/")
    print(f"Health:    {BASE_URL}/health")
    print(f"Info:      {BASE_URL}/info")
    print(f"API Docs:  Ver README.md para endpoints completos")
    
    print("\n🔗 Próximos pasos:")
    print("1. Configurar n8n con las URLs de tu app")
    print("2. Probar workflow completo")
    print("3. Configurar dominio personalizado (opcional)")
    print("4. Monitorear logs en Railway dashboard") 