#!/usr/bin/env python3
"""
Startup script for Under Armour Scraper
Runs initial scraping of new products, then starts the scheduler for daily updates
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_scraper():
    """Run the initial scraper to get new products"""
    logger.info("🚀 Starting initial product scraping...")
    
    try:
        # Run the scraper
        result = subprocess.run([sys.executable, "under_armour_scraper.py"], 
                              capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        if result.returncode == 0:
            logger.info("✅ Initial scraping completed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Initial scraping failed with return code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Initial scraping timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"❌ Error running initial scraper: {e}")
        return False
    
    return True

def run_scheduler():
    """Run the scheduler for daily updates"""
    logger.info("⏰ Starting scheduler for daily updates...")
    
    try:
        # Run the scheduler (this will run indefinitely)
        subprocess.run([sys.executable, "scheduler.py"])
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running scheduler: {e}")

def main():
    """Main startup function"""
    logger.info("🎯 Under Armour Scraper Startup")
    logger.info(f"📅 Started at: {datetime.now()}")
    
    # Check if we're in Heroku environment
    is_heroku = os.environ.get('DYNO') is not None
    logger.info(f"🌐 Environment: {'Heroku' if is_heroku else 'Local'}")
    
    # Run initial scraper
    scraper_success = run_scraper()
    
    if scraper_success:
        logger.info("🎉 Initial scraping completed, starting scheduler...")
        # Start the scheduler for daily updates
        run_scheduler()
    else:
        logger.error("💥 Initial scraping failed, exiting...")
        sys.exit(1)

if __name__ == "__main__":
    main() 