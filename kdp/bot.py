"""Bot Telegram: odpowiada na Twoje komendy (/sprawdz, /moje, /raport …).

Działa w pętli (long polling) – uruchamia go usługa systemd kdp-bot.
Odpowiada wyłącznie na wiadomości z czatu TELEGRAM_CHAT_ID; wszystkie inne pomija.
"""
import logging
import os
import time
from pathlib import Path

import requests

from kdp import notify
from kdp.db import DB
from kdp.http import Fetcher
from kdp.screen import latest_screens
from kdp.watch import add_to_watchlist, load_watchlist, track_watchlist

log = logging.getLogger("kdp")

COMMANDS = [
    ("sprawdz", "sprawdź teraz moje książki na Amazonie"),
    ("moje", "historia moich książek (BSR, opinie, cena)"),
    ("raport", "najlepsze nisze z ostatniej analizy"),
    ("przesiew", "najlepsze frazy z ostatniego przesiewu"),
    ("status", "czy działa tunel i kiedy był ostatni przebieg"),
    ("dodaj", "dodaj książkę: /dodaj ASIN nazwa"),
    ("pomoc", "lista komend"),
]
HELP = ("Komendy:\n" + "\n".join(f"/{c} – {d}" for c, d in COMMANDS)
        + "\n\nNazwy możesz pisać bez polskich znaków, np. /sprawdz.")


def _api(method: str, **params):
    url = notify.API.format(token=os.environ["TELEGRAM_TOKEN"], method=method)
    r = requests.post(url, data=params, timeout=params.get("timeout", 0) + 20)
    r.raise_for_status()
    return r.json().get("result")


def _fmt_int(v):
    return f"{v:,}".replace(",", " ") if isinstance(v, (int, float)) and v else "brak"


def _tail(path: Path, n: int = 1) -> str:
    try:
        lines = [l for l in path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        return "\n".join(lines[-n:]) or "pusty"
    except FileNotFoundError:
        return "brak logu"


class Bot:
    def __init__(self, root: Path, db_path: Path, watch: Path, market: str = "us"):
        self.root, self.db_path, self.watch, self.market = root, db_path, watch, market

    def _db(self):
        return DB(self.db_path)

    # --- komendy -------------------------------------------------------------
    def cmd_pomoc(self, arg):
        return HELP

    cmd_start = cmd_pomoc

    def cmd_sprawdz(self, arg):
        books = load_watchlist(self.watch)
        if not books:
            return "Lista książek jest pusta. Dodaj: /dodaj ASIN nazwa"
        notify.send(f"Sprawdzam {len(books)} książk{'ę' if len(books) == 1 else 'i'} na Amazonie, chwilę…")
        db = self._db()
        res = track_watchlist(Fetcher(db, debug_dir=self.root / "debug"), db, self.market, self.watch, ttl_h=0.5)
        out = []
        for r in res:
            if r.get("error"):
                out.append(f"• {r['label']}: {r['error']}")
                continue
            bsr = _fmt_int(r.get("bsr"))
            if not r.get("bsr"):
                bsr += " (jeszcze bez sprzedaży)"
            price = f"${r['price']:.2f}" if r.get("price") else "brak"
            out.append(f"• {r['label']}\n  BSR: {bsr}\n  opinie: {r.get('reviews') or 0}, cena: {price}"
                       f"\n  https://www.amazon.com/dp/{r['asin']}")
        return "\n".join(out) or "Brak wyników."

    def cmd_moje(self, arg):
        books = load_watchlist(self.watch)
        if not books:
            return "Lista książek jest pusta. Dodaj: /dodaj ASIN nazwa"
        db, out = self._db(), []
        for asin, label in books:
            hist = db.product_history(self.market, asin)[-7:]
            out.append(f"📘 {label or asin}")
            if not hist:
                out.append("  brak danych – użyj /sprawdz")
            for ts, bsr, rev, price, _b, _t in hist:
                out.append(f"  {time.strftime('%d.%m', time.localtime(ts))}: BSR {_fmt_int(bsr)}, opinie {rev or 0}")
        return "\n".join(out)

    def cmd_raport(self, arg):
        n = int(arg) if arg.isdigit() else 10
        rows = self._db().latest_niches(self.market)[:n]
        if not rows:
            return "Brak analizy – pełny przebieg robi się w poniedziałki."
        out = [f"Najlepsze nisze (dane z {rows[0].get('analyzed_at', '?')}):"]
        for i, r in enumerate(rows, 1):
            out.append(f"{i}. {r['keyword']} – ocena {r['score']:.0f}, {r.get('verdict', '')}"
                       f"\n   słabi sprzedający: {r.get('weak_sellers', '-')}, mediana opinii: {r.get('median_reviews', '-')}")
        return "\n".join(out)

    def cmd_przesiew(self, arg):
        n = int(arg) if arg.isdigit() else 15
        rows = latest_screens(self._db(), self.market, n)
        if not rows:
            return "Brak przesiewu."
        out = ["Najlepsze frazy z przesiewu:"]
        for i, (k, s, d, t) in enumerate(rows, 1):
            out.append(f"{i}. {k} – {s:.0f} (kupione/mies.: {d.get('badges_sum', 0)}, słabe: {d.get('low_review_books', 0)})")
        return "\n".join(out)

    def cmd_status(self, arg):
        proxy = os.getenv("KDP_PROXY")
        if proxy:
            try:
                ip = requests.get("https://api.ipify.org", proxies={"http": proxy, "https": proxy}, timeout=15).text
                tunnel = f"działa ✅ (IP {ip})"
            except requests.RequestException:
                tunnel = "NIE DZIAŁA ❌ – sprawdź Luckfoxa"
        else:
            tunnel = "nieustawiony (brak KDP_PROXY)"
        return (f"Tunel przez Luckfoxa: {tunnel}\n\n"
                f"Ostatni przebieg:\n{_tail(self.root / 'logs' / 'run.log')}\n\n"
                f"Ostatnie sprawdzenie książek:\n{_tail(self.root / 'logs' / 'track.log')}")

    def cmd_dodaj(self, arg):
        asin, _, label = arg.strip().partition(" ")
        if not asin:
            return "Użycie: /dodaj ASIN nazwa\nnp. /dodaj B0XXXXXXXX Mileage Log Book"
        return add_to_watchlist(self.watch, asin, label.strip())

    # --- pętla ---------------------------------------------------------------
    def handle(self, text: str) -> str:
        cmd, _, arg = text.strip().partition(" ")
        cmd = cmd.lstrip("/").split("@")[0].lower()
        cmd = cmd.translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
        fn = getattr(self, f"cmd_{cmd}", None)
        if not fn:
            return "Nie znam tej komendy.\n\n" + HELP
        try:
            return fn(arg.strip())
        except Exception as e:   # bot ma działać dalej mimo błędu jednej komendy
            log.exception("Błąd komendy %s", cmd)
            return f"Błąd: {e}"

    def run(self):
        if not notify.configured():
            raise SystemExit("Brak TELEGRAM_TOKEN / TELEGRAM_CHAT_ID w .env – najpierw: kdp_agent.py telegram")
        owner = str(os.environ["TELEGRAM_CHAT_ID"])
        try:
            import json
            _api("setMyCommands", commands=json.dumps([{"command": c, "description": d} for c, d in COMMANDS]))
        except requests.RequestException as e:
            log.warning("setMyCommands: %s", e)
        log.info("Bot działa – czekam na komendy.")
        offset = None
        while True:
            try:
                params = {"timeout": 50}
                if offset:
                    params["offset"] = offset
                updates = _api("getUpdates", **params) or []
            except requests.RequestException as e:
                log.warning("Telegram: %s – ponawiam za 10 s", e)
                time.sleep(10)
                continue
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                text = msg.get("text")
                if not text:
                    continue
                if str(msg.get("chat", {}).get("id")) != owner:
                    log.warning("Pomijam wiadomość z obcego czatu %s", msg.get("chat", {}).get("id"))
                    continue
                log.info("Komenda: %s", text[:60])
                reply = self.handle(text)
                for i in range(0, len(reply), 4000):
                    notify.send(reply[i:i + 4000])
