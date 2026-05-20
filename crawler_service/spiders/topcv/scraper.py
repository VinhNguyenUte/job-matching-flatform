import json
import logging
import os
import random
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOPCV_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

TOPCV_HEADERS = {
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _safe_text(locator, default="N/A"):
    try:
        if locator.count() and locator.first.is_visible():
            text = locator.first.inner_text().strip()
            return text or default
    except Exception:
        pass
    return default


def _human_delay(min_seconds=1.5, max_seconds=3.5):
    time.sleep(random.uniform(min_seconds, max_seconds))


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
            logger.info("Loaded TopCV cookies.json.")
    except Exception as exc:
        logger.error("Could not load TopCV cookies.json: %s", exc)


def _try_cloudflare_click(page, timeout=5000):
    try:
        cf_iframe = page.locator("iframe[title*='Cloudflare'], iframe[src*='cloudflare']")
        if cf_iframe.is_visible(timeout=timeout):
            logger.info("Cloudflare challenge detected on TopCV.")
            time.sleep(2)
            box = cf_iframe.bounding_box()
            if box:
                target_x = box["x"] + 30
                target_y = box["y"] + box["height"] / 2
                page.mouse.move(target_x - 100, target_y - 100, steps=10)
                time.sleep(0.2)
                page.mouse.move(target_x + 15, target_y + 5, steps=10)
                time.sleep(0.3)
                page.mouse.move(target_x, target_y, steps=5)
                time.sleep(0.5)
                page.mouse.click(target_x, target_y, delay=200)
            time.sleep(6)
    except Exception:
        pass


def _is_blocked_page(page):
    try:
        body_text = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        body_text = ""

    blocked_markers = [
        "unable access",
        "unable to access",
        "access denied",
        "you have been blocked",
        "captcha",
        "cloudflare",
        "just a moment",
        "forbidden",
        "403",
    ]
    return any(marker in body_text for marker in blocked_markers)


def _save_block_debug(page, name):
    try:
        page.screenshot(path=f"{name}.png", full_page=True)
    except Exception:
        pass

    try:
        with open(f"{name}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception:
        pass


def _keep_browser_open_if_requested(page):
    if os.getenv("TOPCV_KEEP_OPEN", "false").lower() != "true":
        return

    logger.info("TOPCV_KEEP_OPEN=true, leaving Chrome open for manual testing.")
    logger.info("Current page: %s", page.url)
    try:
        input("Chrome is open. Press Enter here when you want the crawler to close it...")
    except EOFError:
        logger.info("No interactive input available; keeping Chrome open for 60 seconds.")
        time.sleep(60)


def _extract_description(page):
    selectors = [
        ".job-data",
        ".box-info-job .content-tab",
        ".box-info-job",
        ".job-detail__information-detail",
        ".job-detail__information-detail--content",
        ".job-description",
        "[class*='job-description']",
        "[class*='job-detail'] [class*='content']",
        "#tab-detail-job",
        ".content-tab",
        ".box-detail-job",
        "#box-job-detail",
        ".box-job-detail",
        ".job-detail__info--section",
        ".job-detail__section",
        ".job-detail__section--content",
        ".section-body",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.count() and loc.is_visible():
                text = loc.inner_text().strip()
                if len(text) > 80:
                    return text
        except Exception:
            continue

    try:
        text = page.evaluate(
            """
            () => {
                const nodes = Array.from(document.querySelectorAll(
                    'article, section, .box-info-job, .job-data, [class*="description"], [class*="content-tab"], [class*="job-detail"]'
                ));
                const candidates = nodes
                    .map(node => (node.innerText || '').trim())
                    .filter(text => text.length > 120 && text.length < 20000)
                    .sort((a, b) => b.length - a.length);
                return candidates[0] || '';
            }
            """
        )
        if text and len(text.strip()) > 80:
            return text.strip()
    except Exception:
        pass

    return "N/A"


def _extract_quick_view_description(page, card):
    quick_view_selectors = [
        "text=Xem nhanh",
        "button:has-text('Xem nhanh')",
        "a:has-text('Xem nhanh')",
        "[data-original-title*='Xem nhanh']",
        "[title*='Xem nhanh']",
        "[class*='quick-view']",
    ]

    for selector in quick_view_selectors:
        try:
            quick_view = card.locator(selector).first
            if quick_view.count() and quick_view.is_visible():
                quick_view.click(timeout=5000)
                _human_delay(1.5, 3.0)
                break
        except Exception:
            continue
    else:
        return "N/A"

    modal_selectors = [
        ".modal.show .modal-body",
        ".modal.in .modal-body",
        ".modal-dialog .modal-body",
        ".modal-content",
        "#modal-job-detail",
        "[id*='quick-view']",
        "[class*='quick-view']",
        "[class*='job-detail']",
    ]

    description = "N/A"
    for selector in modal_selectors:
        try:
            modal = page.locator(selector).last
            if modal.count() and modal.is_visible():
                text = modal.inner_text().strip()
                if len(text) > 80:
                    description = text
                    break
        except Exception:
            continue

    try:
        close_btn = page.locator(
            ".modal.show button.close, .modal.show .close, "
            ".modal-dialog button.close, .modal-dialog .close, "
            "button:has-text('Đóng'), button:has-text('Close')"
        ).first
        if close_btn.count() and close_btn.is_visible():
            close_btn.click(timeout=3000)
        else:
            page.keyboard.press("Escape")
        _human_delay(0.5, 1.2)
    except Exception:
        pass

    return description


def scrape_topcv_jobs(keyword="IT", location="Vietnam", max_jobs=10, headless=True, target_url=None):
    if target_url:
        url = target_url
        logger.info("Starting TopCV crawl from URL: %s", url)
    else:
        url = f"https://www.topcv.vn/tim-viec-lam-{quote_plus(keyword)}"
        logger.info("Starting TopCV crawl for keyword: %s", keyword)
        logger.info("URL: %s", url)

    jobs_data = []

    with sync_playwright() as p:
        browser = None
        user_data_dir = os.getenv("TOPCV_USER_DATA_DIR")
        context_options = {
            "viewport": {"width": 1280, "height": 800},
            "user_agent": TOPCV_USER_AGENT,
            "extra_http_headers": TOPCV_HEADERS,
            "locale": "vi-VN",
            "timezone_id": "Asia/Ho_Chi_Minh",
        }

        if user_data_dir:
            logger.info("Using persistent TopCV browser profile: %s", user_data_dir)
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                channel=os.getenv("BROWSER_CHANNEL") or None,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
                ignore_default_args=["--enable-automation"],
                **context_options,
            )
        else:
            browser = p.chromium.launch(
                headless=headless,
                channel=os.getenv("BROWSER_CHANNEL") or None,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
                ignore_default_args=["--enable-automation"],
            )
            context = browser.new_context(**context_options)

        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            """
        )

        use_cookie_file = os.getenv("TOPCV_USE_COOKIES", "false").lower() == "true"
        if use_cookie_file and not user_data_dir:
            _load_cookies(context)
        elif not user_data_dir:
            logger.info("Skipping TopCV cookies.json. Set TOPCV_USE_COOKIES=true to enable it.")
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000, referer="https://www.topcv.vn/")
            _try_cloudflare_click(page)
            _human_delay(2.5, 5.0)

            try:
                close_btn = page.locator(".modal-dialog .close, #popup-modal .close, button[aria-label='Close']").first
                if close_btn.count() and close_btn.is_visible():
                    close_btn.click()
                    time.sleep(1)
            except Exception:
                pass

            if _is_blocked_page(page):
                logger.warning("TopCV search page is blocked.")
                _save_block_debug(page, "debug_topcv_blocked_search")
                return jobs_data

            try:
                page.wait_for_selector(".job-item-search-result, .job-item", timeout=10000)
            except Exception:
                logger.warning("No TopCV job cards found. The page may be blocked or still loading.")
                return jobs_data

            last_height = page.evaluate("document.body.scrollHeight")
            while len(jobs_data) < max_jobs:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                _human_delay(2.0, 4.0)

                job_cards = page.locator(".job-item-search-result, .job-item").all()

                for card in job_cards:
                    if len(jobs_data) >= max_jobs:
                        break

                    try:
                        title_el = card.locator("h3 a, .title a, a[href*='/viec-lam/']").first
                        title = _safe_text(title_el)
                        company = _safe_text(card.locator("a.company, .company, [class*='company']").first)
                        location_text = _safe_text(card.locator("label.address, .address, [class*='address']").first)

                        raw_link = title_el.get_attribute("href") if title_el.count() else "N/A"
                        link = raw_link
                        if raw_link != "N/A" and not raw_link.startswith("http"):
                            link = f"https://www.topcv.vn{raw_link}"

                        if not any(job.get("link") == link for job in jobs_data):
                            quick_view_description = _extract_quick_view_description(page, card)
                            jobs_data.append(
                                {
                                    "title": title,
                                    "company": company,
                                    "location": location_text,
                                    "post_time": "N/A",
                                    "link": link,
                                    "description": quick_view_description,
                                }
                            )
                            logger.info("Parsed TopCV listing: %s - %s", title, company)
                    except Exception as exc:
                        logger.debug("Could not parse TopCV job card: %s", exc)

                next_button = page.locator("ul.pagination li a[rel='next'], a.next-page").first
                if next_button.count() and next_button.is_visible():
                    next_button.click()
                    _human_delay(2.5, 5.0)
                else:
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info("No more TopCV jobs to load.")
                        break
                    last_height = new_height

            logger.info("Starting TopCV detail crawl for %s jobs.", len(jobs_data))
            for index, job in enumerate(jobs_data):
                job["seniority_level"] = "N/A"
                job["employment_type"] = "N/A"

                if not job.get("link") or job["link"] == "N/A":
                    job["description"] = "No link"
                    continue

                if job.get("description") and job["description"] != "N/A":
                    logger.info("[%s/%s] Using TopCV quick-view detail: %s", index + 1, len(jobs_data), job["title"])
                    continue

                try:
                    logger.info("[%s/%s] Fetching TopCV detail: %s", index + 1, len(jobs_data), job["title"])
                    page.goto(job["link"], wait_until="domcontentloaded", timeout=30000, referer=url)
                    _try_cloudflare_click(page, timeout=3000)
                    _human_delay(2.0, 4.5)

                    if _is_blocked_page(page):
                        logger.warning("TopCV blocked detail page: %s", job["link"])
                        job["description"] = "Blocked by TopCV"
                        _save_block_debug(page, f"debug_topcv_blocked_{index + 1}")
                        continue

                    job["description"] = _extract_description(page)
                except Exception as exc:
                    logger.error("Could not fetch TopCV detail page: %s", exc)
                    job["description"] = "Detail page load error"

        except Exception as exc:
            logger.error("TopCV crawler failed: %s", exc)
        finally:
            _keep_browser_open_if_requested(page)
            context.close()
            if browser:
                browser.close()

    logger.info("Finished TopCV crawl with %s jobs.", len(jobs_data))
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
        data = scrape_topcv_jobs(
            keyword=item if not is_url else "IT",
            max_jobs=2,
            headless=False,
            target_url=item if is_url else None,
        )
        for job in data:
            print(f"{job['title']} - {job['company']}")
