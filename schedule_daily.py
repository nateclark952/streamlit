"""
Optional: Run the scraper on a daily schedule using Python's schedule library.
This script keeps running and executes the scraper at a specified time each day.
"""

import schedule
import time
from redbeam_scraper import main
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Schedule the scraper to run daily at 9:00 AM
# You can change this time to your preferred time
schedule.every().day.at("09:00").do(main)

logging.info("Redbeam scraper scheduled to run daily at 9:00 AM")
logging.info("Press Ctrl+C to stop the scheduler")

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
except KeyboardInterrupt:
    logging.info("Scheduler stopped by user")

