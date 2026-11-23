"""Szybki przesiew fraz: tylko jedna strona wyników wyszukiwania na frazę (bez stron książek).

Z samej strony wyników mamy: liczbę wyników, opinie, ceny i odznaki „X+ bought in past month”.
To wystarcza, żeby z ~100+ fraz wybrać kilkadziesiąt do pełnej (drogiej) analizy z BSR.
"""
import json
import logging
import math
import os
import time
from statistics import median

from .analyze import search_url
from .db import DB
from .http import Blocked, Fetcher
from .markets import Market
from .parse import parse_serp
from .score import clamp, relevant

log = logging.getLogger("kdp")

SCHEMA = """CREATE TABLE IF NOT EXISTS screens (
    market TEXT, keyword TEXT, ts REAL, score REAL, data TEXT, PRIMARY KEY (market, keyword, ts));"""


def screen_score(items: list[dict], total: int | None, hits: int, keyword: str | None = None) -> dict:
    org_all = [i for i in items if not i["sponsored"]][:16]
    org = [i for i in org_all if i.get("is_book", True)]
    if len(org) < 5:
        return {"score": 0.0, "badges_sum": 0, "with_badge": 0, "low_review_books": len(org),
                "low_with_badge": 0, "median_reviews": 0, "total_results": total, "keyword_hits": hits,
                "sponsored": len(items) - len(org_all), "not_books": True}
    reviews = [i.get("reviews") or 0 for i in org]
    # odznaki liczymy tylko dla produktów pasujących do frazy (nie „Kpop Demon Hunters” dla „hunting”)
    badges = [i["bought_month"] for i in org if i.get("bought_month") and relevant(i.get("title"), keyword)]
    low = [i for i in org if (i.get("reviews") or 0) < 50]
    low_badge = sum(1 for i in low if i.get("bought_month") and relevant(i.get("title"), keyword))
    med_rev = median(reviews) if reviews else 0
    demand = clamp(math.log10(1 + sum(badges)) / 3.5)          # ~3000 kupionych/mies. => 1.0
    entry = clamp(len(low) / 6)                                 # nowi/słabi w topie 16
    competition = clamp(math.log10(1 + med_rev) / 3)            # mediana 1000 opinii => 1.0
    crowd = clamp((math.log10(total) - 2) / 3) if total else 0.5
    score = 100 * (0.35 * demand + 0.25 * entry + 0.20 * (1 - competition)
                   + 0.10 * (1 - crowd) + 0.10 * clamp(hits / 15))
    score += 8 * min(low_badge, 2)  # słaba książka z odznaką sprzedaży – najmocniejszy sygnał
    # Bardzo mało wyników = przypadkowe połączenie słów z podpowiedzi („guitar tab stroller”),
    # a nie nisza, której ktoś szuka – takie frazy nie mogą wygrywać przesiewu.
    if total and total < 300:
        score *= max(0.2, total / 300)
    return {"score": round(min(score, 100), 1), "badges_sum": sum(badges), "with_badge": len(badges),
            "low_review_books": len(low), "low_with_badge": low_badge, "median_reviews": med_rev,
            "total_results": total, "keyword_hits": hits, "sponsored": len(items) - len(org_all)}


def screen_keywords(f: Fetcher, db: DB, m: Market, keywords: list[tuple]) -> list[tuple]:
    """keywords: [(kw, seed, hits, pos)]. Zwraca listę posortowaną wg wyniku przesiewu."""
    db.c.executescript(SCHEMA)
    out, failed = [], 0
    pause = int(os.getenv("KDP_BLOCK_PAUSE", "1200"))
    pauses, max_pauses = 0, int(os.getenv("KDP_MAX_PAUSES", "3"))
    for i, (kw, seed, hits, pos) in enumerate(keywords, 1):
        while True:
            try:
                html = f.get_html(search_url(m, kw), m.lang, ttl_h=24)
                break
            except Blocked:
                if pauses >= max_pauses:
                    log.error("[%s] Przesiew: blokady nie ustępują – kończę na %d/%d frazach.",
                              m.code, i - 1, len(keywords))
                    out.sort(key=lambda x: -x[0])
                    return out
                pauses += 1
                log.warning("[%s] Przesiew: blokada Amazona przy '%s' – przerwa %d min (%d/%d).",
                            m.code, kw, pause // 60, pauses, max_pauses)
                time.sleep(pause)
                f.blocked_count = 0
        if not html:
            failed += 1
            continue
        serp = parse_serp(html)
        if not serp["items"]:
            continue
        r = screen_score(serp["items"], serp["total_results"], hits, kw)
        if r.get("not_books"):  # usuń stare, błędne wyniki pełnej analizy dla tej frazy
            db.c.execute("DELETE FROM niches WHERE market=? AND keyword=?", (m.code, kw))
        db.c.execute("INSERT OR REPLACE INTO screens VALUES (?,?,?,?,?)",
                     (m.code, kw, time.time(), r["score"], json.dumps(r)))
        db.commit()
        out.append((r["score"], (kw, seed, hits, pos), r))
        if i % 20 == 0:
            log.info("[%s] przesiew %d/%d", m.code, i, len(keywords))
    out.sort(key=lambda x: -x[0])
    log.info("[%s] Przesiew gotowy: %d fraz ocenionych, %d nieudanych.", m.code, len(out), failed)
    return out


def latest_screens(db: DB, market: str, limit: int = 30) -> list[tuple]:
    db.c.executescript(SCHEMA)
    rows = db.c.execute("""
        SELECT s.keyword, s.score, s.data, s.ts FROM screens s
        JOIN (SELECT keyword, MAX(ts) ts FROM screens WHERE market=? GROUP BY keyword) l
          ON s.keyword=l.keyword AND s.ts=l.ts
        WHERE s.market=? ORDER BY s.score DESC LIMIT ?""", (market, market, limit)).fetchall()
    return [(k, sc, json.loads(d), t) for k, sc, d, t in rows]
