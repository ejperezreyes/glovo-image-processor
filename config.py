import os
from urllib.parse import urlparse

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Usar SQLite por defecto para simplificar deployment
    # PostgreSQL se puede añadir después si es necesario
    if DATABASE_URL and 'postgresql' in DATABASE_URL:
        # Producción: PostgreSQL (solo si está configurado)
        try:
            url = urlparse(DATABASE_URL)
            DB_CONFIG = {
                'host': url.hostname,
                'port': url.port,
                'database': url.path[1:],  # Remove leading slash
                'user': url.username,
                'password': url.password,
                'type': 'postgresql'
            }
        except:
            # Fallback a SQLite si hay problemas
            DB_CONFIG = {
                'path': 'glovo_products.db',
                'type': 'sqlite'
            }
    else:
        # Por defecto: SQLite (development y producción inicial)
        DB_CONFIG = {
            'path': 'glovo_products.db',
            'type': 'sqlite'
        }
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # External services
    N8N_WEBHOOK_BASE = os.getenv('N8N_WEBHOOK_BASE', 'https://your-n8n-instance.com')
    
    # File storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))
    
    # Business logic
    PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', '0.50'))
    PROCESSING_TIME_PER_IMAGE = int(os.getenv('PROCESSING_TIME_PER_IMAGE', '2'))  # minutes

# Helper function to get database connection
def get_db_connection():
    if Config.DB_CONFIG['type'] == 'postgresql':
        import psycopg2
        return psycopg2.connect(
            host=Config.DB_CONFIG['host'],
            port=Config.DB_CONFIG['port'],
            database=Config.DB_CONFIG['database'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password']
        )
    else:
        import sqlite3
        return sqlite3.connect(Config.DB_CONFIG['path'])

# Production readiness check
def is_production():
    return Config.DATABASE_URL is not None

# Environment info
def get_env_info():
    return {
        'environment': 'production' if is_production() else 'development',
        'database_type': Config.DB_CONFIG['type'],
        'debug': Config.DEBUG,
        'rate_limit': Config.RATE_LIMIT_PER_MINUTE
    } 