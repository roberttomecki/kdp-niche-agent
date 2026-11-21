"""Twoje książki z watch.txt: odczyt listy i sprawdzanie BSR/opinii/ceny."""
import logging
import re
from pathlib import Path

from kdp import notify
from kdp.http import Blocked
from kdp.markets import get_market
from kdp.parse import parse_product

log = logging.getLogger("kdp")
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


def load_watchlist(path: Path) -> list[tuple[str, str]]:
    """watch.txt: jedna książka na linię – ASIN, a po nim opcjonalnie nazwa."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        asin, _, label = line.partition(" ")
        out.append((asin.upper(), label.strip()))
    return out


def add_to_watchlist(path: Path, asin: str, label: str) -> str:
    asin = asin.upper()
    if not ASIN_RE.match(asin):
        return f"„{asin}” nie wygląda na ASIN (10 znaków, np. B0HSCT2JS5)."
    if any(a == asin for a, _ in load_watchlist(path)):
        return f"{asin} już jest na liście."
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + f"{asin} {label}".rstrip() + "\n", encoding="utf-8")
    return f"Dodane: {asin} {label}".rstrip() + ". Będę ją sprawdzał codziennie."


def track_watchlist(f, db, market, path: Path, ttl_h: float = 20) -> list[dict]:
    """Zapisz dzisiejszy BSR, opinie i cenę Twoich książek (historia maks. raz na dobę).

    Zwraca listę wyników: {asin, label, bsr, reviews, price, error}.
    """
    m = get_market(market)
    results = []
    for asin, label in load_watchlist(path):
        res = {"asin": asin, "label": label or asin}
        try:
            page = f.get_html(f"{m.base_url}/dp/{asin}", m.lang, ttl_h=ttl_h)
        except Blocked as e:
            log.error("Śledzenie przerwane: %s", e)
            res["error"] = "Amazon blokuje zapytania – sprawdź tunel (/status)"
            results.append(res)
            return results
        if not page:
            log.warning("[%s] %s: nie udało się pobrać strony", m.code, asin)
            res["error"] = "nie udało się pobrać strony"
            results.append(res)
            continue
        p = parse_product(page)
        p["asin"] = asin
        p["title"] = p.get("title") or label
        hist = db.product_history(m.code, asin)
        prev = hist[-1] if hist else None
        before = len(hist)
        db.add_history(m.code, p)
        db.commit()
        if len(db.product_history(m.code, asin)) > before:   # nowy wpis (maks. raz na dobę)
            for msg in notify.book_events(label or asin, asin, prev, p):
                notify.send(msg)
        res.update(bsr=p.get("bsr"), reviews=p.get("reviews"), price=p.get("price"))
        results.append(res)
        log.info("[%s] moja książka %s: BSR %s, opinie %s", m.code, label or asin, p.get("bsr"), p.get("reviews"))
    return results
