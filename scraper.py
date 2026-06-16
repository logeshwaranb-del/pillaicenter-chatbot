import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from config import (
    WEBSITE_DATA_FILE, SEEN_URLS_FILE, SITEMAPS, INCLUDE_KEYWORDS, 
    EXCLUDE_PATTERNS, SCRAPE_HEADERS, MAX_PAGE_CONTENT
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | scraper | %(message)s")
logger = logging.getLogger(__name__)

# Increased delay for stability
REQUEST_DELAY = 2.0


def get_sitemap_urls(sitemap_url: str, visited: Optional[Set[str]] = None) -> List[str]:
    if visited is None:
        visited = set()
    if sitemap_url in visited:
        return []
    visited.add(sitemap_url)

    urls: List[str] = []
    try:
        logger.info(f"Fetching sitemap: {sitemap_url}")
        resp = requests.get(sitemap_url, headers=SCRAPE_HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml-xml")

        if soup.find("sitemapindex"):
            for sitemap_tag in soup.find_all("sitemap"):
                loc_tag = sitemap_tag.find("loc")
                if loc_tag and loc_tag.text:
                    urls.extend(get_sitemap_urls(loc_tag.text.strip(), visited))
        else:
            for url_tag in soup.find_all("url"):
                loc_tag = url_tag.find("loc")
                if loc_tag and loc_tag.text:
                    urls.append(loc_tag.text.strip())
    except Exception as e:
        logger.error(f"Error fetching sitemap {sitemap_url}: {e}")
    return urls


def is_url_allowed(url: str, site_key: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        path = parsed.path.lower().rstrip("/")

        for pattern in EXCLUDE_PATTERNS:
            if pattern in path or pattern in url.lower():
                return False

        include_kws = INCLUDE_KEYWORDS.get(site_key, [])
        if not any(kw in path for kw in include_kws):
            return False

        if path in ("", "/", "/home"):
            return False
        return True
    except:
        return False


def filter_urls(urls: List[str], site_key: str) -> List[str]:
    seen = set()
    filtered = []
    for u in urls:
        if u not in seen and is_url_allowed(u, site_key):
            seen.add(u)
            filtered.append(u)
    return filtered


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_main_content(html: str, url: str) -> tuple[str, str]:
    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "form", "iframe"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.find(class_=re.compile("content|main|entry", re.I))
        text = main.get_text(separator=" ", strip=True) if main else soup.get_text(separator=" ", strip=True)
        title = soup.find("title").get_text(strip=True) if soup.find("title") else urlparse(url).path
        return title.strip(), clean_text(text)[:MAX_PAGE_CONTENT]
    except:
        return urlparse(url).path, ""


def scrape_page(url: str, max_retries: int = 5) -> Optional[Dict]:
    """
    Scrape with 2-minute timeout and 5 retries
    """
    for attempt in range(max_retries):
        try:
            time.sleep(REQUEST_DELAY)
            resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=120, allow_redirects=True)

            if resp.status_code != 200:
                return None
            if "text/html" not in resp.headers.get("Content-Type", ""):
                return None

            title, content = extract_main_content(resp.text, url)
            if not content or len(content) < 150:
                return None

            return {
                "url": url,
                "title": title,
                "content": content,
                "scraped_at": datetime.utcnow().isoformat() + "Z"
            }

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries} → {url}")
            if attempt == max_retries - 1:
                return None
            time.sleep(6)

        except Exception as e:
            logger.error(f"Error on {url}: {e}")
            return None


def scrape_urls(urls: List[str], desc: str = "Scraping") -> List[Dict]:
    results = []
    for url in tqdm(urls, desc=desc):
        page = scrape_page(url)
        if page:
            results.append(page)
    return results


def full_scrape_and_save() -> List[Dict]:
    logger.info("=== STARTING FULL SCRAPE ===")
    all_pages = []
    all_seen = set()

    for site_key, sitemap_url in SITEMAPS.items():
        raw_urls = get_sitemap_urls(sitemap_url)
        allowed = filter_urls(raw_urls, site_key)
        pages = scrape_urls(allowed, desc=f"Scraping {site_key}")
        all_pages.extend(pages)
        all_seen.update([p["url"] for p in pages])

    # Remove duplicates
    seen = set()
    unique = []
    for p in all_pages:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)

    WEBSITE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WEBSITE_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(all_seen), f, indent=2)

    logger.info(f"=== SCRAPE COMPLETE: {len(unique)} pages saved ===")
    return unique


if __name__ == "__main__":
    print("Running scraper with 2-minute timeout...")
    data = full_scrape_and_save()
    print(f"Done! Total pages: {len(data)}")