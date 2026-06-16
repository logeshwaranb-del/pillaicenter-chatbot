
import json
import logging
from datetime import datetime
from typing import List, Set

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCHEDULER_HOUR, SCHEDULER_MINUTE, SITEMAPS
from scraper import get_sitemap_urls, filter_urls, scrape_urls

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | scheduler | %(message)s")
logger = logging.getLogger(__name__)


def load_seen_urls() -> Set[str]:
    try:
        with open("data/seen_urls.json", "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()


def save_seen_urls(urls: Set[str]):
    with open("data/seen_urls.json", "w", encoding="utf-8") as f:
        json.dump(list(urls), f, indent=2)


def daily_update_job():
    logger.info("=== DAILY UPDATE JOB STARTED ===")
    try:
        current_seen = load_seen_urls()
        new_pages_count = 0

        for site_key, sitemap_url in SITEMAPS.items():
            raw_urls = get_sitemap_urls(sitemap_url)
            allowed = filter_urls(raw_urls, site_key)
            new_urls = [u for u in allowed if u not in current_seen]

            if new_urls:
                logger.info(f"Found {len(new_urls)} new pages for {site_key}")
                pages = scrape_urls(new_urls, desc=f"Scraping {site_key}")
                new_pages_count += len(pages)

                # Update seen URLs
                for p in pages:
                    current_seen.add(p["url"])

        save_seen_urls(current_seen)
        logger.info(f"=== DAILY UPDATE DONE. New pages found: {new_pages_count} ===")

    except Exception as e:
        logger.error(f"Daily update error: {e}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    trigger = CronTrigger(hour=SCHEDULER_HOUR, minute=SCHEDULER_MINUTE)

    scheduler.add_job(
        daily_update_job,
        trigger=trigger,
        id="daily_update",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Next run at {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} IST")
    return scheduler


if __name__ == "__main__":
    print("Testing daily update...")
    daily_update_job()