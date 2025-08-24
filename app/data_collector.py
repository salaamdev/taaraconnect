import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, DataUsageRecord, ApiLog
from app.taara_api import TaaraAPI
from app.config import Config
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.api = TaaraAPI(
            phone_country_code=Config.TAARA_PHONE_COUNTRY_CODE,
            phone_number=Config.TAARA_PHONE_NUMBER,
            passcode=Config.TAARA_PASSCODE,
            partner_id=Config.TAARA_PARTNER_ID,
            hotspot_id=Config.TAARA_HOTSPOT_ID
        )
    
    def log_api_call(self, db: Session, endpoint: str, method: str, 
                     success: bool, status_code: int = None, 
                     response_time_ms: float = 0, error_message: str = None):
        """Log API call to database"""
        log_entry = ApiLog(
            endpoint=endpoint,
            method=method,
            success=success,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message
        )
        db.add(log_entry)
        db.commit()
    
    def collect_data(self):
        """Collect data from Taara API and store in database"""
        db = SessionLocal()
        
        try:
            logger.info("Starting data collection...")
            
            # Get bundle data
            bundle_result = self.api.get_customer_bundle()
            
            # Log API call
            self.log_api_call(
                db=db,
                endpoint="get_customer_bundle",
                method="GET",
                success=bundle_result["success"],
                response_time_ms=bundle_result.get("response_time_ms", 0),
                error_message=bundle_result.get("error")
            )
            
            if bundle_result["success"]:
                # Parse and store data
                parsed_data = self.api.parse_bundle_data(bundle_result["data"])
                
                for record_data in parsed_data:
                    # Create database record
                    db_record = DataUsageRecord(**record_data)
                    db.add(db_record)
                
                db.commit()
                logger.info(f"Successfully stored {len(parsed_data)} data usage records")
                
                # Log out to be nice to the API
                logout_result = self.api.logout()
                self.log_api_call(
                    db=db,
                    endpoint="logout",
                    method="GET",
                    success=logout_result["success"],
                    response_time_ms=logout_result.get("response_time_ms", 0),
                    error_message=logout_result.get("error")
                )
                
                return True
            else:
                logger.error(f"Failed to collect data: {bundle_result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Data collection error: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()

async def run_data_collection():
    """Run data collection asynchronously"""
    collector = DataCollector()
    return collector.collect_data()

if __name__ == "__main__":
    # Run data collection once
    collector = DataCollector()
    collector.collect_data()
