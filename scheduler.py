#!/usr/bin/env python3
"""
Scheduler for Taara data collection
Runs data collection at specified intervals
"""

import schedule
import time
import os
import logging
from datetime import datetime
from app.data_collector import DataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('taara_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_collection():
    """Run data collection job"""
    try:
        logger.info("Starting scheduled data collection...")
        collector = DataCollector()
        success = collector.collect_data()
        
        if success:
            logger.info("Scheduled data collection completed successfully")
        else:
            logger.error("Scheduled data collection failed")
            
    except Exception as e:
        logger.error(f"Error in scheduled data collection: {str(e)}")

def main():
    """Main scheduler function"""
    # Get interval from environment variable (default 15 minutes)
    interval_minutes = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "15"))
    
    logger.info(f"Starting Taara data collection scheduler with {interval_minutes} minute interval")
    
    # Schedule the job
    schedule.every(interval_minutes).minutes.do(run_collection)
    
    # Run once immediately
    run_collection()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
