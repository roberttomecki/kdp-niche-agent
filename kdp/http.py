"""Pobieranie stron: cache w SQLite, opóźnienia, retry, wykrywanie CAPTCHA, proxy."""
import os
import random
import time
import urllib.parse
from pathlib import Path

import requests

from .db import DB

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
]

CAPTCHA_MARKERS = ("/errors/validateCaptcha", "api-services-support@amazon.com",
                   "Enter the characters you see below", "Geben Sie die Zeichen")


class Blocked(Exception):
    pass


class Fetcher:
    """
    Zmienne środowiskowe:
      KDP_PROXY            - np. http://user:pass@host:port (proxy rezydencjalne)
      KDP_FETCH_TEMPLATE   - np. https://api.scraperapi.com?api_key=KEY&url={url}
                             (zewnętrzne API do scrapowania; url jest kodowany)
      KDP_DELAY            - bazowe opóźnienie między stronami w s (domyślnie 4)
    """

    def __init__(self, db: DB, debug_dir: Path | None = None):
        self.db = db
        self.s = requests.Session()
        proxy = os.getenv("KDP_PROXY")
        if proxy:
            self.s.proxies = {"http": proxy, "https": proxy}
        self.template = os.getenv("KDP_FETCH_TEMPLATE")
        self.delay = float(os.getenv("KDP_DELAY", "4"))
        self.debug_dir = debug_dir
        self._last = 0.0
        self.blocked_count = 0

    def _sleep(self, base: float):
        wait = base * random.uniform(0.7, 1.6) - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

    def _headers(self, lang: str):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": f"{lang.replace('_', '-')},{lang[:2]};q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def get_json(self, url: str, params: dict, lang: str, ttl_h: float = 72):
        key = url + "?" + urllib.parse.urlencode(sorted(params.items()))
        cached = self.db.cache_get(key, ttl_h)
        if cached is not None:
            return cached
        self._sleep(0.4)  # autocomplete jest lekki
        for attempt in range(4):
            try:
                r = self.s.get(url, params=params, headers=self._headers(lang), timeout=20)
                if r.status_code == 200:
                    self.db.cache_put(key, r.text)
                    return r.text
                if r.status_code in (429, 503):
                    time.sleep(5 * (attempt + 1))
                    continue
                return None
            except requests.RequestException:
                time.sleep(3 * (attempt + 1))
        return None

    def get_html(self, url: str, lang: str, ttl_h: float = 72) -> str | None:
        cached = self.db.cache_get(url, ttl_h)
        if cached is not None:
            return cached
        target = url
        if self.template:
            target = self.template.format(url=urllib.parse.quote(url, safe=""))
        for attempt in range(3):
            self._sleep(self.delay * (attempt + 1))
            try:
                r = self.s.get(target, headers=self._headers(lang), timeout=60)
            except requests.RequestException:
                continue
            html = r.text
            if r.status_code == 200 and not any(m in html for m in CAPTCHA_MARKERS):
                self.db.cache_put(url, html)
                return html
            if r.status_code == 404:
                return None
            self.blocked_count += 1
            if self.debug_dir:
                self.debug_dir.mkdir(parents=True, exist_ok=True)
                (self.debug_dir / f"blocked_{int(time.time())}.html").write_text(html[:200000])
            time.sleep(20 * (attempt + 1))
        if self.blocked_count >= 6:
            raise Blocked("Amazon blokuje zapytania (CAPTCHA/503). Ustaw KDP_PROXY lub "
                          "KDP_FETCH_TEMPLATE, albo zwiększ KDP_DELAY.")
        return None
