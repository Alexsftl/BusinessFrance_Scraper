from .config import load_config
from .scraper import scrape_offers, cutoff_date
from .relevance import filter_relevant
from .telegram import send_offers
from .store import load_offers, save_offers, new_offers, delete_old

from datetime import datetime
from zoneinfo import ZoneInfo

import logging
import sys
import os

log = logging.getLogger(__name__)


START_HOUR = 8  
END_HOUR = 20


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def within_active_window():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    is_weekday = now.weekday() < 5             
    is_active_hour = START_HOUR <= now.hour <= END_HOUR
    return is_weekday and is_active_hour


def run():
    # 0 - Initialization
    setup_logging()

    force_run = os.environ.get("FORCE_RUN") == "1"

    if not force_run and not within_active_window():
        log.info("Outside active window (Paris time), skipping run.")
        return
    
    config_dict = load_config()
    since = cutoff_date(config_dict["MAX_DAYS"])
    stored = load_offers()

    # 1 - Scraping 
    log.info("Beginning scrapping...")
    scraped = scrape_offers(
        config_dict, since=since, stored=stored, batch=config_dict["BATCH_SIZE"]
    )
    log.info("--- done scrapping")
    fresh = new_offers(scraped, stored)
    log.info(f"--- {len(fresh)} new offers ({len(stored)} already known).")
    merged = {**stored, **fresh}

    # 2 - Relevance
    log.info("Beginning relevancy check...")
    relevant = filter_relevant(merged, config_dict, save_func=save_offers)
    log.info(f"--- {len(relevant)} newly relevant offer(s) to notify.")

    # 3 - Telegram part
    if relevant:
        log.info("Beginning sending offers Telegram...")
        send_offers(relevant, config_dict)
    else:
        log.info("No relevant offers to send through Telegram")

    merged = delete_old(merged, since=since)
    save_offers(merged)

    log.info(f"Run complete: {len(fresh)} new, {len(relevant)} relevant, {len(merged)} stored.")


if __name__ == "__main__":
    run()