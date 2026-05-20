import asyncio
import json
import csv
import re
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

console = Console()

# ──────────────────────────────────────────────────────────────────────────────
# CẤU HÌNH MẶC ĐỊNH
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "headless": True,
    "slow_mo": 60,
    "timeout": 30_000,
    "scroll_pause": 4.0,        
    "scroll_batch_timeout": 12, 
    "max_scroll_empty": 8,      
    "viewport": {"width": 1366, "height": 900},
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "cookies": [],
    "debug": False,
}

VALID_FB_HOSTS = {"www.facebook.com", "m.facebook.com", "facebook.com"}

BLOCKED_PATHS = [
    "/login", "/checkpoint", "/recover", "/two_step",
    "/consent", "/device-based", "/security-check",
]

UI_LABELS = {
    "thích", "like", "bình luận", "comment", "chia sẻ", "share",
    "xem thêm", "see more", "xem thêm nội dung", "đọc thêm",
    "gửi", "send", "theo dõi", "follow", "yêu thích",
    "haha", "wow", "buồn", "phẫn nộ", "thương", "·",
    "tin nhắn", "message", "đặt lịch hẹn",
}


# ──────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ──────────────────────────────────────────────────────────────────────────────
class Comment:
    def __init__(self, author="", text="", timestamp="", likes=0):
        self.author, self.text = author, text
        self.timestamp, self.likes = timestamp, likes

    def to_dict(self):
        return {
            "author": self.author, "text": self.text,
            "timestamp": self.timestamp, "likes": self.likes,
        }


class Post:
    def __init__(self):
        self.post_id = self.author = self.text = ""
        self.timestamp = self.url = ""
        self.likes = self.comments_count = self.shares = 0
        self.comments: list[Comment] = []
        self.scraped_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "post_id": self.post_id, "author": self.author,
            "text": self.text, "timestamp": self.timestamp,
            "likes": self.likes, "comments_count": self.comments_count,
            "shares": self.shares, "url": self.url,
            "comments": [c.to_dict() for c in self.comments],
            "scraped_at": self.scraped_at,
        }


# ──────────────────────────────────────────────────────────────────────────────
# JS HELPERS — chạy trong browser context
# ──────────────────────────────────────────────────────────────────────────────

JS_COUNT_POSTS = """
() => {
    let n = document.querySelectorAll('div[data-pagelet^="FeedUnit"]').length;
    if (n > 0) return n;
    const feed = document.querySelector('div[role="feed"]');
    if (feed) {
        const ch = Array.from(feed.children).filter(
            el => el.tagName === 'DIV' && el.getBoundingClientRect().height > 80
        );
        if (ch.length > 0) return ch.length;
    }
    return Array.from(document.querySelectorAll('div[role="article"]'))
        .filter(el => !el.parentElement.closest('div[role="article"]')
                      && el.getBoundingClientRect().height > 80).length;
}
"""

JS_GET_TEXT = """
(el) => {
    const selectors = [
        '.x1iorvi4.x1yzt60f',
        '[data-ad-preview="message"]',
        '[data-ad-comet-preview="message"]',
        'div[data-testid="post_message"]',
        'div[class*="userContent"]',
    ];
    for (const s of selectors) {
        const target = el.querySelector(s);
        if (target) {
            const t = (target.innerText || '').trim();
            if (t.length > 3) return t;
        }
    }

    const dirEls = Array.from(
        el.querySelectorAll("div[dir='auto'], span[dir='auto']")
    ).filter(e => !e.querySelector("[dir='auto']"));
    let best = '';
    for (const e of dirEls) {
        const t = (e.innerText || '').trim();
        if (t.length > best.length) best = t;
    }
    if (best.length > 3) return best;

    const allDir = Array.from(el.querySelectorAll("[dir='auto']"));
    let best2 = '';
    for (const e of allDir) {
        const t = (e.innerText || '').trim();
        if (t.length > best2.length) best2 = t;
    }
    if (best2.length > 3) return best2;

    const UI = new Set([
        'thích','like','bình luận','comment','chia sẻ','share',
        'xem thêm','see more','xem thêm nội dung','đọc thêm',
        'gửi','send','theo dõi','follow','yêu thích',
        'haha','wow','buồn','phẫn nộ','thương','·',
        'tin nhắn','message','đặt lịch hẹn',
    ]);
    const lines = (el.innerText || '').split('\\n')
        .map(l => l.trim())
        .filter(l => l.length > 3 && !UI.has(l.toLowerCase()));
    if (lines.length > 0) return lines.join('\\n');

    return (el.innerText || '').trim();
}
"""

JS_GET_META = """
(el) => {
    let timestamp = '';
    const abbr = el.querySelector(
        'abbr[data-utime], a[href*="/posts/"] abbr, ' +
        'a[href*="story_fbid"] abbr, a[href*="permalink"] abbr'
    );
    if (abbr) {
        const utime = abbr.getAttribute('data-utime');
        if (utime) {
            timestamp = '__utime__' + utime;
        } else {
            timestamp = (abbr.innerText || '').trim();
        }
    }

    let url = '', post_id = '';
    const link = el.querySelector(
        'a[href*="/posts/"], a[href*="story_fbid"], a[href*="permalink"]'
    );
    if (link) {
        let href = (link.getAttribute('href') || '').trim();
        if (href.startsWith('/')) href = 'https://www.facebook.com' + href;
        url = href;
        const pats = [/\\/posts\\/(\\d+)/, /story_fbid=(\\d+)/, /fbid=(\\d+)/];
        for (const p of pats) {
            const m = href.match(p);
            if (m) { post_id = m[1]; break; }
        }
    }

    if (!post_id || !url) {
        let anc = el;
        while (anc && anc !== document) {
            const attr = anc.getAttribute && (anc.getAttribute('data-ft') || anc.getAttribute('data-store') || '');
            if (attr) {
                try {
                    let parsed = null;
                    const maybe = attr.trim();
                    if ((maybe.startsWith('{') && maybe.endsWith('}')) || maybe.indexOf(':') !== -1) {
                        try {
                            parsed = JSON.parse(maybe);
                        } catch (e) {
                            try {
                                parsed = JSON.parse(maybe.replace(/\\'/g, '"'));
                            } catch (e2) {
                                parsed = null;
                            }
                        }
                    }
                    if (parsed) {
                        const cand = parsed.top_level_post_id || parsed.post_id || parsed.story_fbid || parsed.fbid || parsed.content_owner_id_new;
                        if (cand) {
                            post_id = String(cand);
                            if (!url) url = 'https://www.facebook.com/' + post_id;
                            break;
                        }
                    }
                } catch (err) {}

                const m1 = attr.match(/top_level_post_id" Con?:\\"?(\\d+)/);
                const m2 = attr.match(/story_fbid" Con?:\\"?(\\d+)/);
                const m3 = attr.match(/post_id" Con?:\\"?(\\d+)/);
                const found = m1 || m2 || m3;
                if (found) {
                    post_id = found[1];
                    if (!url) url = 'https://www.facebook.com/' + post_id;
                    break;
                }
            }

            try {
                const alt = anc.querySelector && (anc.querySelector('a[role="link"][href*="/groups/"]') || anc.querySelector('a[href*="permalink.php"]') || anc.querySelector('a[href*="/permalink/"]'));
                if (alt) {
                    let href2 = (alt.getAttribute('href') || '').trim();
                    if (href2.startsWith('/')) href2 = 'https://www.facebook.com' + href2;
                    if (href2) {
                        url = href2;
                        const pats2 = [/\\/posts\\/(\\d+)/, /story_fbid=(\\d+)/, /fbid=(\\d+)/, /permalink\\/(\\d+)/, /permalink.php.*story_fbid=(\\d+)/];
                        for (const p of pats2) {
                            const m = href2.match(p);
                            if (m) { post_id = m[1]; break; }
                        }
                        if (post_id) break;
                    }
                }
            } catch (e) {}

            anc = anc.parentElement;
        }
    }

    let likes = 0;
    const reac = el.querySelector(
        "[aria-label*='reaction'], [aria-label*='Reaction'], " +
        "span[data-testid='UFI2ReactionsCount/root']"
    );
    if (reac) {
        const t = (reac.innerText || '').trim();
        const m = t.replace(/,/g,'').match(/([\\d]+)\\s*([KkMm]?)/);
        if (m) {
            let n = parseFloat(m[1]);
            const s = m[2].toUpperCase();
            if (s === 'K') n *= 1000;
            else if (s === 'M') n *= 1000000;
            likes = Math.round(n);
        }
    }

    let comments_count = 0;
    const commentsText = (el.innerText || '').replace(/,/g, '');
    const cm = commentsText.match(/([\\d]+)\\s*(bình luận|comments?)/i);
    if (cm) comments_count = parseInt(cm[1], 10) || 0;

    let author = '';
    const aEl = el.querySelector('h2 a, h3 a, h4 a, strong a');
    if (aEl) author = (aEl.innerText || '').trim();

    return { timestamp, url, post_id, likes, comments_count, author };
}
"""


# ──────────────────────────────────────────────────────────────────────────────
# SCRAPER CLASS
# ──────────────────────────────────────────────────────────────────────────────
class FacebookScraper:
    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.posts: list[Post] = []
        self._current_page_input = None

    def _build_url(self, page_input: str) -> str:
        if page_input.startswith("http"):
            return page_input
        return f"https://www.facebook.com/{page_input.lstrip('@').strip('/')}"

    async def _launch(self, pw):
        browser = await pw.chromium.launch(
            headless=self.config["headless"],
            slow_mo=self.config["slow_mo"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                f"--window-size={self.config['viewport']['width']},{self.config['viewport']['height']}",
            ],
        )
        context = await browser.new_context(
            user_agent=self.config["user_agent"],
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            viewport=self.config["viewport"],
            extra_http_headers={
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en-US', 'en'] });
        """)

        cookies = self.config.get("cookies", [])
        if cookies:
            clean = []
            for c in cookies:
                if "name" not in c or "value" not in c:
                    continue
                entry = {
                    "name": c["name"], "value": c["value"],
                    "domain": c.get("domain", ".facebook.com"),
                    "path": c.get("path", "/"),
                    "httpOnly": c.get("httpOnly", False),
                    "secure": c.get("secure", True),
                }
                if c.get("sameSite"):
                    entry["sameSite"] = c["sameSite"]
                if c.get("expirationDate"):
                    entry["expires"] = c["expirationDate"]
                clean.append(entry)
            if clean:
                await context.add_cookies(clean)
                console.print(f"  [green]✓ Đã load {len(clean)} cookie[/green]")

        return browser, context

    async def _check_blocked(self, page: Page) -> bool:
        try:
            current_url = page.url
        except Exception:
            return True

        from urllib.parse import urlparse
        parsed = urlparse(current_url)
        if parsed.netloc.lower() not in VALID_FB_HOSTS:
            return True
        if any(parsed.path.lower().startswith(p) for p in BLOCKED_PATHS):
            return True

        blocking_texts = ["đang chờ phê duyệt", "kiểm tra thông báo", "checkpoint", "confirm your identity", "approve this login", "we need to confirm"]
        try:
            page_text = (await page.evaluate("document.body.innerText.toLowerCase()")) or ""
            if any(t in page_text for t in blocking_texts):
                return True
        except Exception:
            pass
        return False

    async def _close_popups(self, page: Page):
        selectors = [
            "[data-cookiebanner='accept_only_essential_button']",
            "button[title='Allow all cookies']",
            "button[title='Decline optional cookies']",
            "[data-testid='cookie-policy-manage-dialog-accept-button']",
        ]
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1200):
                    await btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

    async def _eval(self, page: Page, js: str, arg=None, default=None, retries=2):
        for attempt in range(retries + 1):
            try:
                if arg is not None:
                    return await page.evaluate(js, arg)
                return await page.evaluate(js)
            except Exception as e:
                err = str(e)
                if "context was destroyed" in err or "Target closed" in err:
                    if attempt < retries:
                        try:
                            await page.wait_for_load_state("domcontentloaded", timeout=5_000)
                            await asyncio.sleep(1.0)
                        except Exception:
                            pass
                    else:
                        return default
                else:
                    if self.config.get("debug"):
                        console.print(f"    [dim]eval err ({attempt}): {err[:120]}[/dim]")
                    return default
        return default

    async def _scroll_to_load(self, page: Page, target: int):
        empty_rounds = 0
        max_empty = self.config["max_scroll_empty"]
        batch_timeout = self.config["scroll_batch_timeout"]

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Đang scroll..."),
            BarColumn(),
            TextColumn("[green]{task.completed}/{task.total} bài"),
            console=console,
        ) as progress:
            task = progress.add_task("scroll", total=target)

            while True:
                if await self._check_blocked(page):
                    console.print("\n[red]⚠ Bị Facebook chặn trong khi scroll.[/red]")
                    break

                count_before = (await self._eval(page, JS_COUNT_POSTS, default=0)) or 0
                progress.update(task, completed=min(count_before, target))

                if count_before >= target:
                    break

                await self._eval(page, "window.scrollTo(0, document.body.scrollHeight)")

                deadline = asyncio.get_event_loop().time() + batch_timeout
                count_after = count_before
                while asyncio.get_event_loop().time() < deadline:
                    await asyncio.sleep(1.5)
                    count_after = (await self._eval(page, JS_COUNT_POSTS, default=0)) or 0
                    if count_after > count_before:
                        break

                progress.update(task, completed=min(count_after, target))

                if count_after > count_before:
                    empty_rounds = 0
                else:
                    empty_rounds += 1
                    if empty_rounds >= max_empty:
                        console.print(f"[yellow]⚠ Không tải thêm được bài mới sau {max_empty} lần scroll.[/yellow]")
                        break
                    await asyncio.sleep(self.config["scroll_pause"])

    async def _expand_post(self, page: Page, index: int) -> bool:
        js_expand = """
        async (idx) => {
            const getPosts = () => {
                let p = Array.from(document.querySelectorAll('div[data-pagelet^="FeedUnit"]'));
                if (p.length === 0) {
                    const feed = document.querySelector('div[role="feed"]');
                    if (feed) {
                        p = Array.from(feed.children).filter(
                            el => el.tagName === 'DIV' && el.getBoundingClientRect().height > 80
                        );
                    }
                }
                if (p.length === 0) {
                    p = Array.from(document.querySelectorAll('div[role="article"]')).filter(
                        el => !el.parentElement.closest('div[role="article"]') && el.getBoundingClientRect().height > 80
                    );
                }
                return p;
            };

            const posts = getPosts();
            const el = posts[idx];
            if (!el) return false;

            el.scrollIntoView({ block: 'center' });

            const TEXTS = new Set(['xem thêm', 'see more', 'xem thêm nội dung', 'đọc thêm', 'read more']);
            const candidates = el.querySelectorAll(
                'div[role="button"], span[role="button"], [data-ad-preview="see_more"], [data-ad-comet-preview="see_more"]'
            );
            for (const btn of candidates) {
                const t = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                if (TEXTS.has(t)) {
                    btn.click();
                    await new Promise(r => setTimeout(r, 550));
                }
            }
            return true;
        }
        """
        try:
            await page.evaluate(js_expand, index)
            await asyncio.sleep(0.9)
            return True
        except Exception as e:
            if self.config.get("debug"):
                console.print(f"    [dim]expand err: {e}[/dim]")
            return False

    async def _get_post_data(self, page: Page, index: int, max_retries=3):
        js_extract = f"""
        async (idx) => {{
            const getPosts = () => {{
                let p = Array.from(document.querySelectorAll('div[data-pagelet^="FeedUnit"]'));
                if (p.length === 0) {{
                    const feed = document.querySelector('div[role="feed"]');
                    if (feed) {{
                        p = Array.from(feed.children).filter(
                            el => el.tagName === 'DIV' && el.getBoundingClientRect().height > 80
                        );
                    }}
                }}
                if (p.length === 0) {{
                    p = Array.from(document.querySelectorAll('div[role="article"]')).filter(
                        el => !el.parentElement.closest('div[role="article"]') && el.getBoundingClientRect().height > 80
                    );
                }}
                return p;
            }};

            const posts = getPosts();
            const el = posts[idx];
            if (!el) return null;

            el.scrollIntoView({{ block: 'center', behavior: 'instant' }});
            await new Promise(r => setTimeout(r, 450));

            const getText = {JS_GET_TEXT};
            const getMeta = {JS_GET_META};
            const text = (getText(el) || '').trim();
            const meta = getMeta(el) || {{}};
            return {{ text, meta }};
        }}
        """
        for attempt in range(max_retries):
            try:
                data = await page.evaluate(js_extract, index)
                if data and data.get("text") and len(data["text"].strip()) > 3:
                    return data
                await asyncio.sleep(1.2)
            except Exception as e:
                if self.config.get("debug"):
                    console.print(f"    [dim]Lỗi tại bài {index+1}: {e}[/dim]")
        return None

    async def _get_text_by_index(self, page: Page, index: int) -> str:
        js = f"""
        () => {{
            let posts = Array.from(document.querySelectorAll('div[data-pagelet^="FeedUnit"]'));
            if (posts.length === 0) {{
                const feed = document.querySelector('div[role="feed"]');
                if (feed) posts = Array.from(feed.children).filter(el => el.tagName === 'DIV' && el.getBoundingClientRect().height > 80);
            }}
            if (posts.length === 0) {{
                posts = Array.from(document.querySelectorAll('div[role="article"]')).filter(el => !el.parentElement.closest('div[role="article"]') && el.getBoundingClientRect().height > 80);
            }}
            const el = posts[{index}];
            if (!el) return '';
            const getText = {JS_GET_TEXT};
            return (getText(el) || '').trim();
        }}
        """
        result = await self._eval(page, js, default="")
        return (result or "").strip()

    # ──────────────────────────────────────────────────────
    # HÀM LẤY LINK TỪ NÚT "SAO CHÉP LIÊN KẾT" (CLICK THỰC TẾ TRÊN DIALOG)
    # ──────────────────────────────────────────────────────
    async def _get_share_link_by_index(self, page: Page, index: int) -> str:
        js = f"""
        async (idx) => {{
            let posts = Array.from(document.querySelectorAll('div[data-pagelet^="FeedUnit"]'));
            if (posts.length === 0) {{
                const feed = document.querySelector('div[role="feed"]');
                if (feed) posts = Array.from(feed.children).filter(
                    el => el.tagName === 'DIV' && el.getBoundingClientRect().height > 80
                );
            }}
            if (posts.length === 0) {{
                posts = Array.from(document.querySelectorAll('div[role="article"]'))
                    .filter(el => !el.parentElement.closest('div[role="article"]') && el.getBoundingClientRect().height > 80);
            }}

            const el = posts[idx];
            if (!el) return '';

            // 1. Tìm và click nút "Chia sẻ" ở góc dưới bài viết
            const candidates = Array.from(el.querySelectorAll('div[role="button"], span[role="button"], a[role="button"], [role="button"]'));
            const shareBtn = candidates.find(b => {{
                const t = ((b.innerText || b.textContent || b.getAttribute('aria-label') || '') + '').trim().toLowerCase();
                return t.includes('chia sẻ') || t.includes('share');
            }});
            if (!shareBtn) return '';

            try {{ shareBtn.click(); }} catch (e) {{ return ''; }}
            await new Promise(r => setTimeout(r, 1200)); // Chờ dialog "Chia sẻ lên" mở hẳn

            // 2. Định vị vùng Dialog popup
            const scope = document.querySelector('div[role="dialog"]') || document.querySelector('div[role="menu"]');
            if (!scope) return '';

            // 3. Quét tất cả các phần tử tương tác bên trong Dialog để tìm nút "Sao chép liên kết"
            const menuButtons = Array.from(scope.querySelectorAll('div[role="menuitem"], div[role="button"], span[role="button"], div[style*="cursor: pointer"]'));
            let copyLinkBtn = menuButtons.find(b => {{
                const t = ((b.innerText || b.textContent || b.getAttribute('aria-label') || '') + '').trim().toLowerCase();
                return t.includes('sao chép liên kết') || t.includes('copy link') || t.includes('sao chép liên');
            }});

            // Fallback: Tìm thẻ chứa text rồi lần ngược lên phần tử cha click được
            if (!copyLinkBtn) {{
                const allElements = Array.from(scope.querySelectorAll('*'));
                const targetTextSpan = allElements.find(e => {{
                    const t = (e.innerText || '').trim().toLowerCase();
                    return t === 'sao chép liên kết' || t === 'copy link';
                }});
                if (targetTextSpan) {{
                    copyLinkBtn = targetTextSpan.closest('div[role="button"]') || targetTextSpan.closest('div[role="menuitem"]') || targetTextSpan.parentElement;
                }}
            }}

            if (!copyLinkBtn) return '';

            // 4. Bấm chính xác vào nút "Sao chép liên kết"
            try {{ 
                copyLinkBtn.click(); 
            }} catch (e) {{ 
                return ''; 
            }}
            
            await new Promise(r => setTimeout(r, 800)); // Đợi hệ thống ghi link vào bộ nhớ đệm
            return '__trigger_clipboard__';
        }}
        """
        try:
            # Khởi tạo quyền đọc bộ nhớ đệm cho context của Playwright
            try:
                await page.context.grant_permissions(["clipboard-read", "clipboard-write"])
            except Exception:
                pass

            status = await self._eval(page, js, arg=index, default="")

            # Đọc trực tiếp nội dung chuỗi mà hệ thống vừa nạp vào Clipboard sau cú click chuột
            result_url = ""
            try:
                result_url = await page.evaluate("navigator.clipboard.readText()")
            except Exception:
                pass

            # Đóng hộp thoại Popup bằng nút ESC để dọn DOM thông thoáng cho bài viết tiếp theo
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
            return (result_url or "").strip()
        except Exception:
            return ""

    # ──────────────────────────────────────────────────────
    # PHƯƠNG PHÁP FIX TRIỆT ĐỂ: BÓC TÁCH GIẢI MÃ LINK SHIM (L.PHP) TẦNG PYTHON
    # ──────────────────────────────────────────────────────
    def _clean_facebook_url(self, url: str) -> str:
        if not url:
            return ""
        
        # Nếu chuỗi dính định dạng chuyển hướng bảo mật l.facebook.com hoặc l.php của Facebook
        if "l.facebook.com" in url or "/l.php" in url:
            try:
                # Phân tích cú pháp chuỗi URL query
                parsed_url = urlparse(url)
                queries = parse_qs(parsed_url.query)
                # Tham số 'u' chính là nơi Facebook ẩn giấu URL gốc thực tế bên trong
                if 'u' in queries:
                    decoded_url = unquote(queries['u'][0])
                    # Kiểm tra lại sau giải mã để loại trừ tiếp param rác nếu có
                    if "?" in decoded_url and "facebook.com" not in decoded_url:
                        decoded_url = decoded_url.split("?")[0]
                    return decoded_url.strip()
            except Exception:
                pass
                
        # Làm sạch các token tracking fbclid hoặc thông số app bám đuôi đối với link thường
        if "?" in url and "story_fbid" not in url and "permalink.php" not in url:
            url = url.split("?")[0]
            
        return url.strip()

    async def _extract_posts(self, page: Page, limit: int) -> list[Post]:
        posts = []
        total_in_dom = (await self._eval(page, JS_COUNT_POSTS, default=0)) or 0
        actual_limit = min(total_in_dom, limit)

        console.print(f"[dim]DOM có {total_in_dom} bài, sẽ trích xuất {actual_limit} bài[/dim]")

        if total_in_dom == 0:
            console.print("[red]✗ Không tìm thấy bài nào trong DOM.[/red]")
            return posts

        skipped = 0
        for i in range(actual_limit):
            console.print(f"  [cyan]→ Đang xử lý bài {i+1}/{actual_limit}...[/cyan]", end=" ")

            await self._expand_post(page, i)
            data = await self._get_post_data(page, i, max_retries=3)

            if not data or not data.get("text"):
                skipped += 1
                console.print(f"[yellow]SKIP (không lấy được text)[/yellow]")
                continue

            post = Post()
            text = data.get("text", "").strip()
            meta = data.get("meta", {})
            post.text = text

            if meta:
                ts = meta.get("timestamp", "")
                if ts.startswith("__utime__"):
                    try:
                        utime = int(ts.replace("__utime__", ""))
                        post.timestamp = datetime.fromtimestamp(utime).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        post.timestamp = ts
                else:
                    post.timestamp = ts

                # Đọc link sơ bộ từ mã HTML và giải độc l.php ngay lập tức
                raw_url = meta.get("url", "")
                post.url = self._clean_facebook_url(raw_url)

                # KIỂM TRA ĐIỀU KIỆN FALLBACK QUA NÚT SAO CHÉP LIÊN KẾT
                page_in = getattr(self, '_current_page_input', None)
                group_url = self._build_url(page_in) if page_in else ""
                generic_group_urls = {
                    "https://www.facebook.com/groups",
                    "https://www.facebook.com/groups/",
                    "https://m.facebook.com/groups",
                    "https://m.facebook.com/groups/",
                }
                
                # Nếu URL trống, dính link group tổng hoặc vẫn chưa thoát khỏi cấu trúc l.php rác không chứa ruột
                if (not post.url) or (post.url.rstrip("/") in generic_group_urls) or post.url.rstrip("/").endswith("/groups") or "l.php" in post.url:
                    # Gọi hàm giả lập click nút "Sao chép liên kết" từ Dialog
                    copied_url = await self._get_share_link_by_index(page, i)
                    cleaned_copied_url = self._clean_facebook_url(copied_url)
                    
                    if cleaned_copied_url and "l.php" not in cleaned_copied_url:
                        post.url = cleaned_copied_url
                    else:
                        # Phương án cuối cùng: Tạo chuỗi URL độc lập có index để bảo toàn cấu trúc dữ liệu không bị ghi đè
                        post.url = f"{group_url}/posts/fallback_index_{i}_{datetime.now().strftime('%H%M%S')}" if group_url else "https://www.facebook.com"

                # Cập nhật và chuẩn hóa post_id dựa theo link đích cuối cùng sạch sẽ vừa lấy được
                post.post_id = meta.get("post_id", "")
                if (not post.post_id or "l.php" in post.post_id) and post.url:
                    pats = [r"\/posts\/(\d+)", r"story_fbid=(\d+)", r"fbid=(\d+)", r"permalink\/(\d+)"]
                    for p in pats:
                        m = re.search(p, post.url)
                        if m:
                            post.post_id = m[1]
                            break
                    if not post.post_id:
                        post.post_id = f"fallback_{i}_{datetime.now().strftime('%M%S')}"

                post.likes = meta.get("likes", 0)
                post.comments_count = meta.get("comments_count", 0)
                post.author = meta.get("author", "")

            post.scraped_at = datetime.now().isoformat()
            posts.append(post)

            preview = text[:80].replace("\n", " ")
            if len(text) > 80:
                preview += "..."
            console.print(f"[green]✓[/green] {preview}")

            await asyncio.sleep(0.3)

        if skipped:
            console.print(f"\n[yellow]⚠ Bỏ qua {skipped} bài (không lấy được text). Chạy với --debug để xem chi tiết.[/yellow]")

        return posts

    async def _scrape_comments(self, page: Page, post: Post, max_comments: int):
        if not post.url or "fallback_index_" in post.url:
            return
        try:
            await page.goto(post.url, wait_until="domcontentloaded", timeout=self.config["timeout"])
            await asyncio.sleep(2)
            await self._close_popups(page)

            await self._expand_post(page, 0)
            full = await self._get_text_by_index(page, 0)
            if full and len(full) > len(post.text):
                post.text = full

            for _ in range(6):
                clicked = False
                for label in ["Xem thêm bình luận", "View more comments", "More comments"]:
                    try:
                        btn = page.locator(f"text={label}").first
                        if await btn.is_visible(timeout=1000):
                            await btn.click()
                            await asyncio.sleep(1.5)
                            clicked = True
                    except Exception:
                        pass
                if not clicked:
                    break

            comment_els = await page.query_selector_all("div[aria-label*='Comment'], div[aria-label*='comment'], div[data-testid='UFI2Comment/root_depth_0']")
            for el in comment_els[:max_comments]:
                try:
                    author_el = await el.query_selector("a[role='link'] span, h3 a, h4 a")
                    text_el = await el.query_selector("div[dir='auto']")
                    author = (await author_el.inner_text()).strip() if author_el else "Unknown"
                    text = (await text_el.inner_text()).strip() if text_el else ""
                    if text and text != author:
                        post.comments.append(Comment(author=author, text=text))
                except Exception:
                    continue
        except Exception as e:
            console.print(f"  [yellow]⚠ Lỗi comments bài {post.post_id}: {e}[/yellow]")

    async def scrape(self, page_input: str, num_posts: int = 10, scrape_comments: bool = False, max_comments: int = 20) -> list[Post]:
        url = self._build_url(page_input)
        has_cookies = bool(self.config.get("cookies"))

        console.print(Panel(
            f"[bold cyan]Facebook Scraper — No-Skip Edition[/bold cyan]\n"
            f"Trang   : [yellow]{url}[/yellow]\n"
            f"Số bài  : [green]{num_posts}[/green]  |  Comments: [green]{'Có' if scrape_comments else 'Không'}[/green]\n"
            f"Cookie  : [green]{'✓ Đã load' if has_cookies else '✗ Không có — dễ bị chặn'}[/green]",
            border_style="cyan"
        ))

        async with async_playwright() as pw:
            browser, context = await self._launch(pw)
            page = await context.new_page()

            console.print("[cyan]→ Đang mở trang Facebook...[/cyan]")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.config["timeout"])
            except Exception as e:
                console.print(f"[red]Không thể mở trang: {e}[/red]")
                await browser.close()
                return []

            await asyncio.sleep(2.5)
            await self._close_popups(page)

            if await self._check_blocked(page):
                console.print("\n[red]✗ Facebook đang chặn / yêu cầu xác minh.[/red]")
                await browser.close()
                return []

            console.print(f"[cyan]→ Đang scroll để tải đủ {num_posts} bài...[/cyan]")
            await self._scroll_to_load(page, num_posts)

            console.print("\n[cyan]→ Đang trích xuất bài đăng...[/cyan]")
            self._current_page_input = page_input
            self.posts = await self._extract_posts(page, num_posts)

            if scrape_comments and self.posts:
                console.print(f"\n[cyan]→ Cào comments ({len(self.posts)} bài)...[/cyan]")
                for idx, post in enumerate(self.posts):
                    console.print(f"  Bài {idx+1}/{len(self.posts)}...")
                    await self._scrape_comments(page, post, max_comments)

            await browser.close()
            try:
                self._current_page_input = None
            except Exception:
                pass

        console.print(f"\n[bold green]✓ Hoàn tất! Cào được {len(self.posts)}/{num_posts} bài.[/bold green]")
        return self.posts


# ──────────────────────────────────────────────────────────────────────────────
# XUẤT FILE & PHẦN CLI CÒN LẠI
# ──────────────────────────────────────────────────────────────────────────────
def export_json(posts: list[Post], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in posts], f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓ JSON:[/green] {path}")


def export_csv(posts: list[Post], path: str):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["post_id", "author", "timestamp", "text", "likes", "comments_count", "shares", "url", "scraped_at"])
        for p in posts:
            w.writerow([p.post_id, p.author, p.timestamp, p.text, p.likes, p.comments_count, p.shares, p.url, p.scraped_at])
    console.print(f"[green]✓ CSV:[/green] {path}")


def export_comments_csv(posts: list[Post], path: str):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["post_id", "post_preview", "author", "comment", "timestamp", "likes"])
        for p in posts:
            for c in p.comments:
                w.writerow([p.post_id, p.text[:80], c.author, c.text, c.timestamp, c.likes])
    console.print(f"[green]✓ Comments CSV:[/green] {path}")


def display_results(posts: list[Post]):
    t = Table(title="Kết quả cào dữ liệu", show_lines=True, border_style="cyan")
    t.add_column("#", style="dim", width=4)
    t.add_column("Nội dung bài", max_width=60)
    t.add_column("Thời gian", style="yellow", width=20)
    t.add_column("Lượt thích", style="green", justify="right", width=12)
    t.add_column("Comments", style="blue", justify="right", width=10)
    for i, p in enumerate(posts, 1):
        preview = p.text[:80].replace("\n", " ")
        if len(p.text) > 80:
            preview += "..."
        t.add_row(str(i), preview, p.timestamp or "N/A", str(p.likes), str(len(p.comments)))
    console.print(t)


def parse_args():
    parser = argparse.ArgumentParser(description="Cào bài đăng Facebook công khai — không bỏ sót bài")
    parser.add_argument("--page", help="Tên trang hoặc URL Facebook (1 trang)")
    parser.add_argument("--pages-file", help="File chứa danh sách trang (1 trang/dòng)")
    parser.add_argument("--posts", type=int, default=10, help="Số bài cần cào (mặc định: 10)")
    parser.add_argument("--comments", action="store_true", help="Cào comments")
    parser.add_argument("--max-comments", type=int, default=20)
    parser.add_argument("--format", choices=["json", "csv", "both"], default="json")
    parser.add_argument("--output", default="output", help="Tiền tố file output")
    parser.add_argument("--visible", action="store_true", help="Hiện trình duyệt")
    parser.add_argument("--debug", action="store_true", help="In DOM info + innerText thô")
    parser.add_argument("--cookies", help="Đường dẫn file cookies.json")
    return parser.parse_args()


def load_cookies(cookie_path: Path) -> list[dict]:
    raw = json.loads(cookie_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("cookies.json phải là một mảng")

    SAME_SITE_MAP = {"no_restriction": "None", "norestriction": "None", "no-restriction": "None", "lax": "Lax", "strict": "Strict", "none": "None", "unspecified": "Lax", "": None}
    VALID_SAME_SITE = {"Strict", "Lax", "None"}

    cookies = []
    for c in raw:
        if not isinstance(c, dict) or "name" not in c or "value" not in c:
            continue
        entry = {
            "name": c["name"], "value": c["value"],
            "domain": c.get("domain", ".facebook.com"), "path": c.get("path", "/"),
            "httpOnly": bool(c.get("httpOnly", False)), "secure": bool(c.get("secure", True)),
        }
        ss = str(c.get("sameSite") or c.get("same_site") or "").strip()
        if ss in VALID_SAME_SITE:
            entry["sameSite"] = ss
        elif ss.lower() in SAME_SITE_MAP:
            mapped = SAME_SITE_MAP[ss.lower()]
            if mapped: entry["sameSite"] = mapped
        if c.get("expirationDate"):
            entry["expires"] = float(c["expirationDate"])
        cookies.append(entry)
    return cookies


async def main():
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
    args = parse_args()

    pages = []
    if args.pages_file:
        pf = Path(args.pages_file)
        if not pf.exists():
            console.print(f"[red]Không tìm thấy file: {args.pages_file}[/red]")
            return
        pages = [line.strip() for line in pf.read_text(encoding="utf-8").split("\n") if line.strip()]
    elif args.page:
        pages = [args.page]
    else:
        console.print("[red]Cần --page hoặc --pages-file[/red]")
        return

    if not pages: return

    cookies = []
    cookie_path = Path(args.cookies) if args.cookies else (Path("cookies.json") if Path("cookies.json").exists() else None)

    if cookie_path and cookie_path.exists():
        try:
            cookies = load_cookies(cookie_path)
            console.print(f"[green]✓ Load {len(cookies)} cookie từ {cookie_path}[/green]")
        except Exception as e:
            console.print(f"[red]Lỗi đọc file cookie: {e}[/red]")
            return

    scraper = FacebookScraper(config={"headless": not args.visible, "debug": args.debug, "cookies": cookies})

    all_posts = []
    for idx, page in enumerate(pages, 1):
        console.print(f"\n[cyan]══════════════════════════════════════[/cyan]")
        console.print(f"[cyan]Trang {idx}/{len(pages)}: {page}[/cyan]")
        console.print(f"[cyan]══════════════════════════════════════[/cyan]")
        try:
            posts = await scraper.scrape(page_input=page, num_posts=args.posts, scrape_comments=args.comments, max_comments=args.max_comments)
            if posts: all_posts.extend(posts)
        except Exception as e:
            console.print(f"[red]✗ Lỗi cào {page}: {e}[/red]")

    if not all_posts: return

    console.print(f"\n[bold green]✓ Hoàn tất! Tổng cộng {len(all_posts)} bài từ {len(pages)} trang.[/bold green]")
    display_results(all_posts)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{args.output}_{ts}"
    raw_json_path = f"{base}.json" if args.format in ("json", "both") else None

    if raw_json_path: export_json(all_posts, raw_json_path)
    if args.format in ("csv", "both"):
        export_csv(all_posts, f"{base}_posts.csv")
        if args.comments: export_comments_csv(all_posts, f"{base}_comments.csv")

if __name__ == "__main__":
    asyncio.run(main())