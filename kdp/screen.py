"""Szybki przesiew fraz: tylko jedna strona wyników wyszukiwania na frazę (bez stron książek).

Z samej strony wyników mamy: liczbę wyników, opinie, ceny i odznaki „X+ bought in past month”.
To wystarcza, żeby z ~100+ fraz wybrać kilkadziesiąt do pełnej (drogiej) analizy z BSR.
"""
import json
import logging
import math
import time
from statistics import median

from .analyze import search_url
from .db import DB
from .http import Fetcher
from .markets import Market
from .parse import parse_serp
from .score import clamp

log = logging.getLogger("kdp")

SCHEMA = """CREATE TABLE IF NOT EXISTS screens (
    market TEXT, keyword TEXT, ts REAL, score REAL, data TEXT, PRIMARY KEY (market, keyword, ts));"""


def screen_score(items: list[dict], total: int | None, hits: int) -> dict:
    org = [i for i in items if not i["sponsored"]][:16]
    reviews = [i.get("reviews") or 0 for i in org]
    badges = [i["bought_month"] for i in org if i.get("bought_month")]
    low = [i for i in org if (i.get("reviews") or 0) < 50]
    low_badge = sum(1 for i in low if i.get("bought_month"))
    med_rev = median(reviews) if reviews else 0
    demand = clamp(math.log10(1 + sum(badges)) / 3.5)          # ~3000 kupionych/mies. => 1.0
    entry = clamp(len(low) / 6)                                 # nowi/słabi w topie 16
    competition = clamp(math.log10(1 + med_rev) / 3)            # mediana 1000 opinii => 1.0
    crowd = clamp((math.log10(total) - 2) / 3) if total else 0.5
    score = 100 * (0.35 * demand + 0.25 * entry + 0.20 * (1 - competition)
                   + 0.10 * (1 - crowd) + 0.10 * clamp(hits / 15))
    score += 8 * min(low_badge, 2)  # słaba książka z odznaką sprzedaży – najmocniejszy sygnał
    return {"score": round(min(score, 100), 1), "badges_sum": sum(badges), "with_badge": len(badges),
            "low_review_books": len(low), "low_with_badge": low_badge, "median_reviews": med_rev,
            "total_results": total, "keyword_hits": hits, "sponsored": len(items) - len(org)}


def screen_keywords(f: Fetcher, db: DB, m: Market, keywords: list[tuple]) -> list[tuple]:
    """keywords: [(kw, seed, hits, pos)]. Zwraca listę posortowaną wg wyniku przesiewu."""
    db.c.executescript(SCHEMA)
    out = []
    for i, (kw, seed, hits, pos) in enumerate(keywords, 1):
        html = f.get_html(search_url(m, kw), m.lang, ttl_h=24)
        if not html:
            continue
        serp = parse_serp(html)
        if not serp["items"]:
            continue
        r = screen_score(serp["items"], serp["total_results"], hits)
        db.c.execute("INSERT OR REPLACE INTO screens VALUES (?,?,?,?,?)",
                     (m.code, kw, time.time(), r["score"], json.dumps(r)))
        db.commit()
        out.append((r["score"], (kw, seed, hits, pos), r))
        if i % 20 == 0:
            log.info("[%s] przesiew %d/%d", m.code, i, len(keywords))
    out.sort(key=lambda x: -x[0])
    return out


def latest_screens(db: DB, market: str, limit: int = 30) -> list[tuple]:
    db.c.executescript(SCHEMA)
    rows = db.c.execute("""
        SELECT s.keyword, s.score, s.data, s.ts FROM screens s
        JOIN (SELECT keyword, MAX(ts) ts FROM screens WHERE market=? GROUP BY keyword) l
          ON s.keyword=l.keyword AND s.ts=l.ts
        WHERE s.market=? ORDER BY s.score DESC LIMIT ?""", (market, market, limit)).fetchall()
    return [(k, sc, json.loads(d), t) for k, sc, d, t in rows]
