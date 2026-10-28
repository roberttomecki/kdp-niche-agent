"""Analiza konkurencji dla frazy: SERP + strony produktów -> ocena niszy."""
import logging
import urllib.parse

from .db import DB
from .http import Fetcher
from .markets import Market
from .parse import parse_product, parse_serp
from .score import sales_per_day, score_niche

log = logging.getLogger("kdp")


def search_url(m: Market, kw: str) -> str:
    return f"{m.base_url}/s?k={urllib.parse.quote_plus(kw)}&i=stripbooks"


def analyze_keyword(f: Fetcher, db: DB, m: Market, kw: str, hits: int = 0,
                    top_n: int = 10, product_ttl_h: float = 72) -> dict | None:
    html = f.get_html(search_url(m, kw), m.lang, ttl_h=24)
    if not html:
        log.warning("Brak wyników wyszukiwania dla '%s'", kw)
        return None
    serp = parse_serp(html)
    if not serp["items"]:
        log.warning("0 wyników sparsowanych dla '%s' – możliwa zmiana HTML Amazona", kw)
        if f.debug_dir:
            f.debug_dir.mkdir(parents=True, exist_ok=True)
            (f.debug_dir / f"serp_{m.code}_{kw[:40].replace(' ', '_')}.html").write_text(html)
        return None

    organic = [i for i in serp["items"] if not i["sponsored"]][:top_n]
    products = []
    for item in organic:
        p = db.get_product(m.code, item["asin"], product_ttl_h)
        if p is None:
            page = f.get_html(f"{m.base_url}/dp/{item['asin']}", m.lang, ttl_h=product_ttl_h)
            p = parse_product(page) if page else {}
            db.save_product(m.code, item["asin"], p)
        merged = {**item, **{k: v for k, v in p.items() if v not in (None, "")}}
        merged["est_sales_day"] = round(sales_per_day(merged.get("bsr"), m.sales_factor), 2)
        products.append(merged)

    db.save_serp(m.code, kw, serp["total_results"], serp["items"])
    result = score_niche(products, serp["total_results"], m.sales_factor, hits)
    result["sponsored_count"] = sum(1 for i in serp["items"] if i["sponsored"])
    result["top_products"] = [
        {k: p.get(k) for k in ("asin", "title", "price", "reviews", "rating", "bsr",
                               "est_sales_day", "pages", "pub_date", "indie")}
        for p in products]
    db.save_niche(m.code, kw, result["score"], result)
    db.commit()
    return result
