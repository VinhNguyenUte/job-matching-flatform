import json
import logging
import os
import sys
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Detect if running inside Docker/Linux to adjust browser config
_IS_LINUX = sys.platform.startswith("linux")

LINKEDIN_USER_AGENT = (
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
            logger.info("Loaded LinkedIn cookies.json.")
    except Exception as exc:
        logger.error("Could not load LinkedIn cookies.json: %s", exc)


def _extract_job_id(raw_link):
    if not raw_link or raw_link == "N/A":
        return None

    try:
        base_path = raw_link.split("?")[0].strip("/")
        parts = [part for part in base_path.split("/") if part]
        if "view" in parts:
            candidate = parts[parts.index("view") + 1]
        else:
            candidate = parts[-1].split("-")[-1]
        return candidate if candidate.isdigit() else None
    except Exception:
        return None


def _normalize_link(raw_link, card=None):
    if raw_link and raw_link != "N/A":
        if not raw_link.startswith("http"):
            raw_link = "/" + raw_link.lstrip("/")
            raw_link = f"https://www.linkedin.com{raw_link}"

        job_id = _extract_job_id(raw_link)
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
        return raw_link

    try:
        job_id = card.get_attribute("data-job-id") if card else None
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
    except Exception:
        pass

    return "N/A"


def _extract_description_from_panel(page):
    import time
    try:
        # Nhấn "Show more" trên trang khách (guest page) nếu có
        show_more = page.locator("button.show-more-less-html__button, button.see-more-jobs-core__show-more").first
        if show_more.count() and show_more.is_visible(timeout=500):
            show_more.click(timeout=1000)
            time.sleep(0.5)
    except Exception:
        pass

    try:
        about_text = page.evaluate(
            """
            () => {
                const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const isAboutHeading = (value) => {
                    const text = normalize(value).toLowerCase();
                    return text === 'about the job' || text === 'về công việc' || text === 've cong viec';
                };

                const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,span,div'))
                    .filter((node) => isAboutHeading(node.innerText || node.textContent));

                for (const heading of headings) {
                    let node = heading.parentElement;
                    for (let depth = 0; node && depth < 6; depth += 1, node = node.parentElement) {
                        const fullText = normalize(node.innerText);
                        if (fullText.length < 100) continue;

                        const lines = fullText
                            .split('\\n')
                            .map((line) => line.trim())
                            .filter(Boolean);
                        const headingIndex = lines.findIndex(isAboutHeading);
                        if (headingIndex >= 0 && headingIndex < lines.length - 1) {
                            return lines.slice(headingIndex + 1).join('\\n').trim();
                        }

                        const withoutHeading = fullText
                            .replace(/^about the job\\s*/i, '')
                            .replace(/^về công việc\\s*/i, '')
                            .replace(/^ve cong viec\\s*/i, '')
                            .trim();
                        if (withoutHeading.length > 80) return withoutHeading;
                    }
                }

                const detail = document.querySelector(
                    '#job-details, div.jobs-description-content__text, div.show-more-less-html__markup'
                );
                if (!detail) return '';

                const detailText = normalize(detail.innerText || detail.textContent);
                return detailText
                    .replace(/^about the job\\s*/i, '')
                    .replace(/^về công việc\\s*/i, '')
                    .replace(/^ve cong viec\\s*/i, '')
                    .trim();
            }
            """
        )
        if about_text and len(about_text.strip()) > 80:
            return about_text.strip()
    except Exception:
        pass

    selectors = [
        "div.jobs-description-content__text",
        "#job-details",
        "div.show-more-less-html__markup",
        "article.jobs-description__container",
        "section.jobs-description",
        "[class*='jobs-description']",
        "article",
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

    return "N/A"


def _get_panel_description_text(page):
    """Read whatever description text is currently in the panel (fast, no wait)."""
    selectors = [
        "#job-details",
        "div.jobs-description-content__text",
        "div.show-more-less-html__markup",
        "article.jobs-description__container",
        "section.jobs-description",
        "[class*='jobs-description']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=500):
                text = loc.inner_text(timeout=500).strip()
                if len(text) > 30:
                    return text
        except Exception:
            pass
    return ""


def _wait_for_panel_content_change(page, previous_text, timeout_ms=4000):
    """Wait until the panel description text is different from previous_text."""
    start = time.time()
    while time.time() - start < (timeout_ms / 1000.0):
        current = _get_panel_description_text(page)
        if current and current != previous_text:
            return True
        time.sleep(0.25)
    return False


def _extract_criteria_from_panel(page):
    criteria = {
        "seniority_level": "N/A",
        "employment_type": "N/A",
        "job_function": "N/A",
        "industries": "N/A",
    }

    try:
        items = page.locator(
            "ul.description__job-criteria-list > li, "
            "ul.job-details-jobs-unified-top-card__job-insight-view-model-secondary > li, "
            "div.job-details-preferences-and-skills div.job-details-jobs-unified-top-card__job-insight"
        ).all()
    except Exception:
        items = []

    for item in items:
        try:
            text = item.inner_text().strip()
            lowered = text.lower()
            if "seniority" in lowered or "entry level" in lowered or "mid-senior" in lowered:
                criteria["seniority_level"] = text
            elif "employment" in lowered or "full-time" in lowered or "part-time" in lowered:
                criteria["employment_type"] = text
            elif "function" in lowered:
                criteria["job_function"] = text
            elif "industries" in lowered or "industry" in lowered:
                criteria["industries"] = text
        except Exception:
            continue

    return criteria


def _is_auth_or_blocked(page):
    try:
        text = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        text = ""

    markers = [
        "sign in",
        "join linkedin",
        "authwall",
        "captcha",
        "security verification",
        "something went wrong",
        "access denied",
    ]
    return any(marker in text for marker in markers)


def scrape_linkedin_jobs(keyword="IT", location="Vietnam", max_jobs=10, headless=True, target_url=None):
    if target_url:
        url = target_url
        logger.info("Starting LinkedIn crawl from URL: %s", url)
    else:
        url = (
            "https://www.linkedin.com/jobs/search?"
            f"keywords={quote_plus(keyword)}&location={quote_plus(location)}&sortBy=DD&f_TPR=r604800"
        )
        logger.info("Starting LinkedIn crawl for keyword=%s location=%s", keyword, location)
        logger.info("URL: %s", url)

    jobs_data = []

    # In Docker/Linux: no BROWSER_CHANNEL (only Chromium is installed via playwright)
    browser_channel = None if _IS_LINUX else (os.getenv("BROWSER_CHANNEL") or None)

    launch_args = ["--disable-blink-features=AutomationControlled", "--disable-infobars"]
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
            user_agent=LINKEDIN_USER_AGENT,
            locale="en-US",
            timezone_id="Asia/Ho_Chi_Minh",
        )

        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            """
        )

        _load_cookies(context)
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            card_selector = (
                "ul.jobs-search__results-list > li, "
                "li.jobs-search-results__list-item, "
                "div[data-job-id], "
                "div.job-card-container"
            )

            try:
                page.wait_for_selector(card_selector, timeout=10000)
            except Exception:
                logger.warning("No LinkedIn job cards found. Login may be required.")
                return jobs_data

            last_height = 0
            retries = 0
            seen = set()

            while len(jobs_data) < max_jobs and retries < 5:
                try:
                    page.evaluate(
                        """
                        window.scrollTo(0, document.body.scrollHeight);
                        const el = document.querySelector('.jobs-search-results-list');
                        if (el) el.scrollTo(0, el.scrollHeight);
                        """
                    )
                except Exception:
                    time.sleep(3)
                    retries += 1
                    continue

                time.sleep(2.5)

                try:
                    see_more_button = page.locator("button.infinite-scroller__show-more-button-active").first
                    if see_more_button.count() and see_more_button.is_visible():
                        see_more_button.click()
                        time.sleep(2)
                except Exception:
                    pass

                job_cards = page.locator(card_selector).all()
                new_jobs_found = False

                for card in job_cards:
                    if len(jobs_data) >= max_jobs:
                        break

                    try:
                        link_el = card.locator("a[href*='/jobs/view/'], a.base-card__full-link").first
                        raw_link = link_el.get_attribute("href") if link_el.count() else "N/A"
                        link = _normalize_link(raw_link, card)
                        if link in seen or link == "N/A":
                            continue

                        title = _safe_text(
                            card.locator(
                                "h3.base-search-card__title, "
                                "a.job-card-list__title, "
                                "a.job-card-container__link strong, "
                                "strong"
                            ).first
                        )
                        company = _safe_text(
                            card.locator(
                                "h4.base-search-card__subtitle, "
                                "span.job-card-container__primary-description, "
                                ".job-card-container__company-name, "
                                "a.hidden-nested-link"
                            ).first
                        )
                        loc = _safe_text(
                            card.locator(
                                "span.job-search-card__location, "
                                "ul.job-card-container__metadata-wrapper li, "
                                ".job-card-container__metadata-item"
                            ).first
                        )
                        post_time = "N/A"
                        time_el = card.locator("time").first
                        if time_el.count() and time_el.is_visible():
                            post_time = time_el.get_attribute("datetime") or time_el.inner_text().strip()

                        # Snapshot current panel text BEFORE clicking
                        prev_panel_text = _get_panel_description_text(page)

                        try:
                            card.click(timeout=5000)
                        except Exception:
                            try:
                                link_el.click(timeout=5000)
                            except Exception:
                                pass

                        description = "N/A"
                        criteria = {
                            "seniority_level": "N/A",
                            "employment_type": "N/A",
                            "job_function": "N/A",
                            "industries": "N/A",
                        }

                        if _wait_for_panel_content_change(page, prev_panel_text, timeout_ms=4000):
                            description = _extract_description_from_panel(page)
                            criteria = _extract_criteria_from_panel(page)
                        else:
                            logger.info("Panel did not change after click for '%s', will fallback", title)


                        seen.add(link)
                        jobs_data.append(
                            {
                                "title": title,
                                "company": company,
                                "location": loc,
                                "post_time": post_time,
                                "link": link,
                                "description": description,
                                **criteria,
                            }
                        )
                        new_jobs_found = True
                        logger.info("Parsed LinkedIn job listing: %s - %s", title, company)
                    except Exception as exc:
                        logger.debug("Could not parse LinkedIn card: %s", exc)

                try:
                    new_height = page.evaluate(
                        """
                        let h = document.body.scrollHeight;
                        const el = document.querySelector('.jobs-search-results-list');
                        if (el) h += el.scrollHeight;
                        h;
                        """
                    )
                except Exception:
                    new_height = last_height

                if new_height == last_height and not new_jobs_found:
                    retries += 1
                    if retries >= 3:
                        logger.info("No more LinkedIn jobs to load.")
                        break
                else:
                    retries = 0

                last_height = new_height

            # Fallback for cards that did not expose a panel description.
            for index, job in enumerate(jobs_data):
                if job.get("description") and job["description"] != "N/A":
                    continue

                try:
                    logger.info("[%s/%s] Fallback LinkedIn detail: %s", index + 1, len(jobs_data), job["title"])
                    try:
                        page.goto(job["link"], wait_until="domcontentloaded", timeout=45000)
                    except Exception as e:
                        logger.warning("Timeout or error navigating to %s, proceeding anyway: %s", job["link"], e)
                    
                    time.sleep(3.0)
                    if _is_auth_or_blocked(page):
                        job["description"] = "LinkedIn requires login or blocked detail page"
                        continue

                    job["description"] = _extract_description_from_panel(page)
                    job.update(_extract_criteria_from_panel(page))
                except Exception as exc:
                    logger.error("Could not fetch LinkedIn detail page: %s", exc)
                    job["description"] = "Detail page load error"

        except Exception as exc:
            logger.error("LinkedIn crawler failed: %s", exc)
        finally:
            browser.close()

    logger.info("Finished LinkedIn crawl with %s jobs.", len(jobs_data))
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
        data = scrape_linkedin_jobs(
            keyword=item if not is_url else "IT",
            max_jobs=2,
            headless=False,
            target_url=item if is_url else None,
        )
        for job in data:
            print(f"{job['title']} - {job['company']}")
