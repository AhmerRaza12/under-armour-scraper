import os
import sys
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from daily_update import main as daily_update_main

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_daily_update():
    """Run the daily update function"""
    try:
        logger.info("Starting scheduled daily update")
        daily_update_main()
        logger.info("Scheduled daily update completed")
    except Exception as e:
        logger.error(f"Error in scheduled daily update: {e}")

def main():
    """Main scheduler function"""
    scheduler = BlockingScheduler()
    
    # Schedule daily update at 1am Pacific Time
    pacific_tz = pytz.timezone('America/Los_Angeles')
    scheduler.add_job(
        run_daily_update,
        CronTrigger(hour=1, minute=0, timezone=pacific_tz),
        id='daily_update',
        name='Daily Under Armour Product Update',
        replace_existing=True
    )
    
    logger.info("Scheduler started. Daily updates will run at 1am Pacific Time.")
    logger.info("Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
        scheduler.shutdown()

if __name__ == "__main__":
    main() 