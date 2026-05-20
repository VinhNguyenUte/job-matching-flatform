import json
import logging
import os
import sys
import time

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Detect if running inside Docker/Linux to adjust browser config
_IS_LINUX = sys.platform.startswith("linux")

# User agent that matches the OS running the browser
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
) if _IS_LINUX else (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _safe_text(locator, default="N/A"):
    try:
        if locator.count() and locator.first.is_visible():
            text = locator.first.inner_text().strip()
            return text or default
    except Exception:
        pass
    return default


def _extract_description_from_panel(page):
    selectors = [
        ".job-details__paragraph",
        ".job-details__description",
        ".job-description",
        "[class*='job-description']",
        "[class*='job-details']",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.count() and loc.is_visible():
                text = loc.inner_text().strip()
                if len(text) > 50:
                    return text
        except Exception:
            continue

    try:
        text = page.evaluate(
            """
            () => {
                const heading = Array.from(document.querySelectorAll('h1,h2,h3,h4'))
                    .find(el => /job description/i.test((el.innerText || '').trim()));
                if (!heading) return '';

                let node = heading.parentElement;
                for (let depth = 0; node && depth < 5; depth += 1, node = node.parentElement) {
                    const value = (node.innerText || '').trim();
                    if (value.length > 80 && value.length < 12000) return value;
                }
                return '';
            }
            """
        )
        if text and len(text.strip()) > 50:
            return text.strip()
    except Exception:
        pass

    return "N/A"


def _wait_for_panel_load(page, expected_title, timeout_ms=3000):
    start_time = time.time()
    normalized_expected = "".join(c for c in expected_title.lower() if c.isalnum())
    if not normalized_expected:
        return True

    title_selectors = [
        ".job-details__title",
        ".job-details h1",
        "h1.job-details__title",
        ".job-view h1",
        "h1"
    ]

    while time.time() - start_time < (timeout_ms / 1000.0):
        for sel in title_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    val = loc.inner_text().strip()
                    normalized_val = "".join(c for c in val.lower() if c.isalnum())
                    if normalized_expected in normalized_val or normalized_val in normalized_expected:
                        logger.info("Panel matched title: %s", val)
                        return True
            except Exception:
                pass
        time.sleep(0.3)
    return False


def _load_cookies(context):
    cookies_path = os.path.join(os.path.dirname(__file__), "cookies.json")
    if not os.path.exists(cookies_path):
        return

    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            raw_cookies = json.load(f)

        valid_cookies = []
        if isinstance(raw_cookies, list):
            for cookie in raw_cookies:
                if "name" in cookie and "value" in cookie and "domain" in cookie:
                    valid_cookies.append(
                        {
                            "name": cookie["name"],
                            "value": cookie["value"],
                            "domain": cookie["domain"],
                            "path": cookie.get("path", "/"),
                        }
                    )
        elif isinstance(raw_cookies, dict) and "cookies" in raw_cookies:
            valid_cookies = raw_cookies["cookies"]

        if valid_cookies:
            context.add_cookies(valid_cookies)
            logger.info("Loaded ITviec cookies.json.")
    except Exception as exc:
        logger.error("Could not load ITviec cookies.json: %s", exc)


def _try_cloudflare_click(page, timeout=5000):
    try:
        cf_iframe = page.locator("iframe[title*='Cloudflare'], iframe[src*='cloudflare']")
        if cf_iframe.is_visible(timeout=timeout):
            logger.info("Cloudflare challenge detected on ITviec.")
            box = cf_iframe.bounding_box()
            if box:
                target_x = box["x"] + 30
                target_y = box["y"] + box["height"] / 2
                page.mouse.move(target_x, target_y, steps=10)
                time.sleep(0.5)
                page.mouse.click(target_x, target_y, delay=200)
            time.sleep(6)
    except Exception:
        pass


def scrape_itviec_jobs(keyword="IT", location="Vietnam", max_jobs=10, headless=False, target_url=None):
    if target_url:
        url = target_url
        logger.info("Starting ITviec crawl from URL: %s", url)
    else:
        url = f"https://itviec.com/it-jobs/{keyword}"
        logger.info("Starting ITviec crawl for keyword: %s", keyword)
        logger.info("URL: %s", url)

    jobs_data = []

    # In Docker/Linux: no BROWSER_CHANNEL (only Chromium is installed via playwright)
    # On Windows: optionally use chrome channel if BROWSER_CHANNEL env is set
    browser_channel = None if _IS_LINUX else (os.getenv("BROWSER_CHANNEL") or None)

    # Extra args required for headless mode in Docker (no sandbox, shared memory fix)
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
    ]
    if _IS_LINUX:
        launch_args += [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
        ]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            channel=browser_channel,
            args=launch_args,
            ignore_default_args=["--enable-automation"],
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=_USER_AGENT,
        )

        stealth = Stealth()
        stealth.apply_stealth_sync(context)
        _load_cookies(context)

        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            _try_cloudflare_click(page)
            time.sleep(3)

            try:
                page.wait_for_selector(".job-card", timeout=10000)
            except Exception:
                logger.warning("No ITviec job cards found. The page may be blocked or still loading.")
                return jobs_data

            last_height = page.evaluate("document.body.scrollHeight")
            seen = set()

            while len(jobs_data) < max_jobs:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                job_cards = page.locator(".job-card").all()

                for card in job_cards:
                    if len(jobs_data) >= max_jobs:
                        break

                    try:
                        title = _safe_text(card.locator("h3").first)
                        company = _safe_text(card.locator("a[href*='/companies/']:not(.logo-employer-card)").first)
                        location_text = _safe_text(card.locator(".d-flex.align-items-center .ims-1").first)
                        if location_text == "N/A":
                            location_text = _safe_text(card.locator("text=/Da Nang|Ho Chi Minh|Ha Noi|Remote/i").first)

                        dedupe_key = (title, company, location_text)
                        if dedupe_key in seen:
                            continue

                        link_el = card.locator("a[href*='/it-jobs/']").first
                        if not link_el.count():
                            link_el = card.locator("h3 a, a").first
                        
                        raw_link = link_el.get_attribute("href") if link_el.count() else "N/A"
                        link = raw_link
                        if raw_link != "N/A" and not raw_link.startswith("http"):
                            link = f"https://itviec.com{raw_link}"

                        try:
                            card.click(timeout=5000)
                            time.sleep(1.0)
                        except Exception:
                            pass

                        description = "N/A"
                        if _wait_for_panel_load(page, title, timeout_ms=3000):
                            description = _extract_description_from_panel(page)
                        else:
                            logger.info("Panel did not load expected title: '%s', will fallback to detail page", title)

                        seen.add(dedupe_key)
                        jobs_data.append(
                            {
                                "title": title,
                                "company": company,
                                "location": location_text,
                                "post_time": "N/A",
                                "link": link,
                                "description": description,
                                "seniority_level": "N/A",
                                "employment_type": "N/A",
                            }
                        )
                        logger.info("Parsed ITviec job: %s - %s", title, company)
                    except Exception as exc:
                        logger.debug("Could not parse ITviec job card: %s", exc)

                next_button = page.locator("a[rel='next']").first
                if next_button.count() and next_button.is_visible():
                    next_button.click()
                    time.sleep(3)
                else:
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info("No more ITviec jobs to load.")
                        break
                    last_height = new_height

            # Fallback for cards that did not expose a panel description.
            for index, job in enumerate(jobs_data):
                if job.get("description") and job["description"] != "N/A" and job["link"] != "N/A":
                    continue

                try:
                    logger.info("[%s/%s] Fallback ITviec detail: %s", index + 1, len(jobs_data), job["title"])
                    page.goto(job["link"], wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2.0)
                    _try_cloudflare_click(page, timeout=3000)
                    job["description"] = _extract_description_from_panel(page)
                except Exception as exc:
                    logger.error("Could not fetch ITviec detail page: %s", exc)
                    job["description"] = "Detail page load error"

            logger.info("Finished ITviec detail scraping for %s jobs.", len(jobs_data))

        except Exception as exc:
            logger.error("ITviec crawler failed: %s", exc)
        finally:
            browser.close()

    logger.info("Finished ITviec crawl with %s jobs.", len(jobs_data))
    return jobs_data


if __name__ == "__main__":
    urls_file = os.path.join(os.path.dirname(__file__), "urls.txt")
    inputs = []
    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            inputs = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not inputs:
        inputs = ["Python"]

    for item in inputs:
        print(f"\nProcessing input: {item}")
        is_url = item.startswith("http")
        data = scrape_itviec_jobs(
            keyword=item if not is_url else "IT",
            max_jobs=2,
            headless=False,
            target_url=item if is_url else None,
        )
        for job in data:
            print(f"{job['title']} - {job['company']}")
