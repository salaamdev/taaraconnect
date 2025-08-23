import os

class Settings:
    database_url: str = "sqlite:///./taara_monitoring.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "your-secret-key-change-this"
    
    # Taara API Configuration
    taara_phone_country_code: str = "254"
    taara_phone_number: str = "718920243"
    taara_passcode: str = "888344"
    taara_partner_id: str = "313324693"
    taara_hotspot_id: str = "596370186"
    
    # Scraping Configuration
    scraping_interval_minutes: int = 15
    
    # API URLs
    taara_login_url: str = "https://share.taara.company/v1/users/subscriber/login"
    taara_bundle_url: str = "https://share.taara.company/v1/customers/get-customer-bundle"
    taara_hotspot_config_url: str = "https://share.taara.company/v1/hotspot/GetHotspotConfig"
    taara_logout_url: str = "https://share.taara.company/v1/users/subscriber/logout"
    
    debug: bool = True

    def __init__(self):
        # Load from environment variables
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.redis_url = os.getenv("REDIS_URL", self.redis_url)
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.taara_phone_country_code = os.getenv("TAARA_PHONE_COUNTRY_CODE", self.taara_phone_country_code)
        self.taara_phone_number = os.getenv("TAARA_PHONE_NUMBER", self.taara_phone_number)
        self.taara_passcode = os.getenv("TAARA_PASSCODE", self.taara_passcode)
        self.taara_partner_id = os.getenv("TAARA_PARTNER_ID", self.taara_partner_id)
        self.taara_hotspot_id = os.getenv("TAARA_HOTSPOT_ID", self.taara_hotspot_id)
        self.scraping_interval_minutes = int(os.getenv("SCRAPING_INTERVAL_MINUTES", self.scraping_interval_minutes))
        self.debug = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()
