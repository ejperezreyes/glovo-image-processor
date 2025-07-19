import os
from urllib.parse import urlparse

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # En Railway, PostgreSQL se provee automáticamente
    if DATABASE_URL and 'postgresql' in DATABASE_URL:
        # Producción: PostgreSQL
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
        except Exception as e:
            # Fallback a SQLite si hay problemas
            print(f"Warning: PostgreSQL config failed, using SQLite: {e}")
            DB_CONFIG = {
                'path': 'glovo_products.db',
                'type': 'sqlite'
            }
    else:
        # Desarrollo: SQLite
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
        try:
            import psycopg2
            return psycopg2.connect(
                host=Config.DB_CONFIG['host'],
                port=Config.DB_CONFIG['port'],
                database=Config.DB_CONFIG['database'],
                user=Config.DB_CONFIG['user'],
                password=Config.DB_CONFIG['password']
            )
        except Exception as e:
            print(f"PostgreSQL connection failed, falling back to SQLite: {e}")
            import sqlite3
            return sqlite3.connect('glovo_products.db')
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