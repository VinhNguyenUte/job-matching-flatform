import asyncio
import json
import logging
import os
import time
from pathlib import Path

import schedule

from spiders.facebook.scraper import FacebookScraper, load_cookies
from spiders.itviec.scraper import scrape_itviec_jobs
from spiders.linkedin.scraper import scrape_linkedin_jobs
from publisher import publish_jobs, publish_facebook_posts

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _read_inputs(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def scrape_facebook_posts(base_spiders_dir, is_headless):
    facebook_dir = Path(base_spiders_dir) / "facebook"
    pages_file = facebook_dir / "pages.txt"

    if not pages_file.exists():
        logger.info("Facebook pages.txt not found, skipping facebook spider.")
        return []

    pages = [
        line.strip()
        for line in pages_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not pages:
        logger.info("Facebook pages.txt is empty, skipping facebook spider.")
        return []

    cookies = []
    cookies_file = facebook_dir / "cookies.json"
    if cookies_file.exists():
        try:
            cookies = load_cookies(cookies_file)
            logger.info("Loaded %s Facebook cookies.", len(cookies))
        except Exception as exc:
            logger.error("Could not load Facebook cookies: %s", exc)

    max_posts = int(os.getenv("FACEBOOK_MAX_POSTS", "3"))
    scrape_comments = os.getenv("FACEBOOK_SCRAPE_COMMENTS", "false").lower() == "true"
    max_comments = int(os.getenv("FACEBOOK_MAX_COMMENTS", "20"))

    scraper = FacebookScraper(
        config={
            "headless": is_headless,
            "debug": os.getenv("FACEBOOK_DEBUG", "false").lower() == "true",
            "cookies": cookies,
        }
    )

    all_posts = []
    for page_name in pages:
        try:
            logger.info("Running facebook spider for: %s", page_name)
            posts = await scraper.scrape(
                page_input=page_name,
                num_posts=max_posts,
                scrape_comments=scrape_comments,
                max_comments=max_comments,
            )
            all_posts.extend([post.to_dict() for post in posts])
        except Exception as exc:
            logger.error("Facebook spider failed for %s: %s", page_name, exc)

    return all_posts


def scrape_job_sites(base_spiders_dir, is_headless):
    all_jobs = []
    spider_dirs = ["linkedin", "itviec"]

    for spider_name in spider_dirs:
        urls_file = os.path.join(base_spiders_dir, spider_name, "urls.txt")
        inputs = _read_inputs(urls_file)

        if not inputs:
            logger.info("No inputs found for %s, skipping.", spider_name)
            continue

        for input_str in inputs:
            logger.info("Running %s spider for input: %s", spider_name, input_str)

            is_url = input_str.startswith("http")
            target_url = input_str if is_url else None
            keyword = input_str if not is_url else "IT"

            if spider_name == "linkedin":
                jobs = scrape_linkedin_jobs(keyword=keyword, max_jobs=10, headless=is_headless, target_url=target_url)
            elif spider_name == "itviec":
                jobs = scrape_itviec_jobs(keyword=keyword, max_jobs=10, headless=is_headless, target_url=target_url)
            else:
                jobs = []

            all_jobs.extend(jobs)

    return all_jobs


def job():
    logger.info("Starting crawler cronjob.")
    try:
        is_headless = os.getenv("HEADLESS", "false").lower() == "true"
        base_spiders_dir = os.path.join(os.path.dirname(__file__), "spiders")

        all_jobs = scrape_job_sites(base_spiders_dir, is_headless)
        if all_jobs:
            output_file = os.path.join("data", "latest_jobs.json")
            _save_json(output_file, all_jobs)
            logger.info("Saved %s jobs to %s", len(all_jobs), output_file)

            if os.getenv("ENABLE_RABBITMQ_PUBLISH", "false").lower() == "true":
                try:
                    publish_jobs(all_jobs)
                except Exception as e:
                    logger.error("Failed to publish jobs to RabbitMQ: %s", e)
        else:
            logger.info("No jobs collected in this run.")

        facebook_posts = asyncio.run(scrape_facebook_posts(base_spiders_dir, is_headless))
        if facebook_posts:
            output_file = os.path.join("data", "latest_facebook_posts.json")
            _save_json(output_file, facebook_posts)
            logger.info("Saved %s Facebook posts to %s", len(facebook_posts), output_file)

            if os.getenv("ENABLE_RABBITMQ_PUBLISH", "false").lower() == "true":
                try:
                    publish_facebook_posts(facebook_posts)
                except Exception as e:
                    logger.error("Failed to publish FB posts to RabbitMQ: %s", e)
        else:
            logger.info("No Facebook posts collected in this run.")

    except Exception as exc:
        logger.error("Crawler cronjob failed: %s", exc)


if __name__ == "__main__":
    logger.info("Starting Crawler Service.")

    job()

    schedule.every(1).hours.do(job)
    logger.info("Crawler Service scheduled to run every 1 hour.")

    while True:
        schedule.run_pending()
        time.sleep(60)
