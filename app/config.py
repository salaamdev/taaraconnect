"""
Configuration management for Taara Internet Monitor
Handles environment variables and application settings
"""

import os
import secrets
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration settings"""
    
    # =============================================================================
    # TAARA API CREDENTIALS
    # =============================================================================
    TAARA_PHONE_COUNTRY_CODE: str = os.getenv("TAARA_PHONE_COUNTRY_CODE", "254")
    TAARA_PHONE_NUMBER: str = os.getenv("TAARA_PHONE_NUMBER", "")
    TAARA_PASSCODE: str = os.getenv("TAARA_PASSCODE", "")
    TAARA_PARTNER_ID: str = os.getenv("TAARA_PARTNER_ID", "")
    TAARA_HOTSPOT_ID: str = os.getenv("TAARA_HOTSPOT_ID", "")
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/taara_monitoring.db")
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    # Timezone settings
    TIMEZONE: str = os.getenv("TIMEZONE", "Africa/Nairobi")  # East Africa Time (UTC+3)
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # =============================================================================
    # DATA COLLECTION SETTINGS
    # =============================================================================
    COLLECTION_INTERVAL: int = int(os.getenv("COLLECTION_INTERVAL", "900"))
    SCRAPING_INTERVAL_MINUTES: int = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "15"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    # API Rate Limiting
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))
    API_BURST_LIMIT: int = int(os.getenv("API_BURST_LIMIT", "20"))
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "https://localhost").split(",")
    
    # SSL/TLS
    SSL_CERT_PATH: str = os.getenv("SSL_CERT_PATH", "/etc/nginx/ssl/cert.pem")
    SSL_KEY_PATH: str = os.getenv("SSL_KEY_PATH", "/etc/nginx/ssl/key.pem")
    SSL_VERIFY: bool = os.getenv("SSL_VERIFY", "True").lower() == "true"
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = os.getenv("ENABLE_SECURITY_HEADERS", "True").lower() == "true"
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))
    CSP_POLICY: str = os.getenv("CSP_POLICY", "default-src 'self'")
    
    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "100"))
    CONNECTION_TIMEOUT: int = int(os.getenv("CONNECTION_TIMEOUT", "30"))
    KEEPALIVE_TIMEOUT: int = int(os.getenv("KEEPALIVE_TIMEOUT", "65"))
    
    # Cache Settings
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # =============================================================================
    # MONITORING & LOGGING
    # =============================================================================
    ENABLE_HEALTH_CHECK: bool = os.getenv("ENABLE_HEALTH_CHECK", "True").lower() == "true"
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
    
    # Logging
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE_MAX_SIZE: int = int(os.getenv("LOG_FILE_MAX_SIZE", "10485760"))
    LOG_FILE_BACKUP_COUNT: int = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
    
    # Metrics
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    METRICS_ENDPOINT: str = os.getenv("METRICS_ENDPOINT", "/metrics")
    ENABLE_REQUEST_LOGGING: bool = os.getenv("ENABLE_REQUEST_LOGGING", "True").lower() == "true"
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    # Email
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_TLS: bool = os.getenv("EMAIL_TLS", "True").lower() == "true"
    
    # Webhooks
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    
    # Third-party APIs
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ANALYTICS_API_KEY: str = os.getenv("ANALYTICS_API_KEY", "")
    
    # =============================================================================
    # DOCKER & DEPLOYMENT
    # =============================================================================
    DOCKER_IMAGE_TAG: str = os.getenv("DOCKER_IMAGE_TAG", "latest")
    CONTAINER_NAME: str = os.getenv("CONTAINER_NAME", "taara-monitor")
    DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "taara-network")
    
    # Health Check URLs
    HEALTH_CHECK_URL: str = os.getenv("HEALTH_CHECK_URL", "http://localhost:8000/api/data")
    EXTERNAL_HEALTH_CHECK_URL: str = os.getenv("EXTERNAL_HEALTH_CHECK_URL", "")
    
    # =============================================================================
    # BACKUP & MAINTENANCE
    # =============================================================================
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "True").lower() == "true"
    BACKUP_INTERVAL: int = int(os.getenv("BACKUP_INTERVAL", "86400"))
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_STORAGE_PATH: str = os.getenv("BACKUP_STORAGE_PATH", "/app/backups")
    
    # Database Maintenance
    AUTO_VACUUM_ENABLED: bool = os.getenv("AUTO_VACUUM_ENABLED", "True").lower() == "true"
    AUTO_VACUUM_INTERVAL: int = int(os.getenv("AUTO_VACUUM_INTERVAL", "604800"))
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    ENABLE_API_DOCS: bool = os.getenv("ENABLE_API_DOCS", "False").lower() == "true"
    ENABLE_DEBUG_ROUTES: bool = os.getenv("ENABLE_DEBUG_ROUTES", "False").lower() == "true"
    ENABLE_MAINTENANCE_MODE: bool = os.getenv("ENABLE_MAINTENANCE_MODE", "False").lower() == "true"
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "True").lower() == "true"
    
    # Experimental Features
    ENABLE_REAL_TIME_UPDATES: bool = os.getenv("ENABLE_REAL_TIME_UPDATES", "False").lower() == "true"
    ENABLE_ADVANCED_ANALYTICS: bool = os.getenv("ENABLE_ADVANCED_ANALYTICS", "False").lower() == "true"
    ENABLE_MOBILE_APP_API: bool = os.getenv("ENABLE_MOBILE_APP_API", "False").lower() == "true"
    
    @classmethod
    def validate_required_settings(cls) -> List[str]:
        """Validate that required settings are present"""
        missing = []
        
        # Check required Taara credentials
        if not cls.TAARA_PHONE_NUMBER:
            missing.append("TAARA_PHONE_NUMBER")
        if not cls.TAARA_PASSCODE:
            missing.append("TAARA_PASSCODE")
        if not cls.TAARA_PARTNER_ID:
            missing.append("TAARA_PARTNER_ID")
        if not cls.TAARA_HOTSPOT_ID:
            missing.append("TAARA_HOTSPOT_ID")
        
        return missing
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def get_database_dir(cls) -> Path:
        """Get database directory path"""
        if cls.DATABASE_URL.startswith("sqlite:///"):
            db_path = cls.DATABASE_URL.replace("sqlite:///", "")
            return Path(db_path).parent
        return Path("./data")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        dirs_to_create = [
            cls.get_database_dir(),
            Path("./logs"),
            Path(cls.BACKUP_STORAGE_PATH) if cls.BACKUP_STORAGE_PATH else Path("./backups")
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)

# Global configuration instance
config = Config()

# Validate configuration on import
missing_settings = config.validate_required_settings()
if missing_settings and config.is_production():
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Missing required settings: {', '.join(missing_settings)}")

# Ensure required directories exist
config.ensure_directories()
