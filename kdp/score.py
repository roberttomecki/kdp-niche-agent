"""Szacowanie sprzedaży z BSR i ocena niszy (0-100).

Wszystko tu to heurystyki – służą do porównywania nisz między sobą,
a nie do przewidywania dokładnej sprzedaży.
"""
import math
from statistics import median

# BSR -> sprzedane egzemplarze/dzień, książki drukowane amazon.com (zgrubne punkty orientacyjne)
BSR_CURVE = [(1, 4000), (10, 1200), (100, 300), (1_000, 70), (5_000, 25), (10_000, 15),
             (50_000, 4), (100_000, 1.5), (200_000, 0.7), (500_000, 0.25),
             (1_000_000, 0.1), (3_000_000, 0.02), (10_000_000, 0.003)]


def sales_per_day(bsr: int | None, factor: float = 1.0) -> float:
    if not bsr or bsr <= 0:
        return 0.0
    pts = BSR_CURVE
    if bsr <= pts[0][0]:
        return pts[0][1] * factor
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if bsr <= x2:  # interpolacja log-log
            t = (math.log(bsr) - math.log(x1)) / (math.log(x2) - math.log(x1))
            return math.exp(math.log(y1) + t * (math.log(y2) - math.log(y1))) * factor
    return pts[-1][1] * factor


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def score_niche(products: list[dict], total_results: int | None, factor: float,
                keyword_hits: int = 0) -> dict:
    """products: organiczne wyniki z top N, każdy z polami bsr, reviews, price, indie."""
    with_bsr = [p for p in products if p.get("bsr")]
    bsrs = [p["bsr"] for p in with_bsr]
    sales = [sales_per_day(b, factor) for b in bsrs]
    reviews = [p.get("reviews") or 0 for p in products]
    prices = [p["price"] for p in products if p.get("price")]

    med_bsr = median(bsrs) if bsrs else None
    sellers = sum(1 for s in sales if s >= 0.7)  # ~ BSR 200k na amazon.com
    # „Słabi, a sprzedają”: mało opinii, a dobry BSR -> da się wejść
    weak_sellers = sum(1 for p in with_bsr if (p.get("reviews") or 0) < 50
                       and sales_per_day(p["bsr"], factor) >= 0.5)
    med_reviews = median(reviews) if reviews else 0
    indie_share = sum(1 for p in products if p.get("indie")) / len(products) if products else 0

    n = max(len(products), 1)
    demand = clamp(math.log10(1 + sum(sales)) / 2.0)            # ~100 szt./dzień w top N => 1.0
    demand_breadth = clamp(sellers / n * 1.5)                     # ilu w top sprzedaje regularnie
    comp_results = clamp((math.log10(total_results) - 2) / 3) if total_results else 0.5  # 100 .. 100k
    comp_reviews = clamp(math.log10(1 + med_reviews) / 3)         # mediana 1000 opinii => 1.0
    opportunity = clamp(weak_sellers / n * 2.5)
    popularity = clamp(keyword_hits / 15)                         # z autocomplete

    score = 100 * (0.25 * demand + 0.15 * demand_breadth + 0.25 * opportunity
                   + 0.10 * popularity + 0.10 * indie_share
                   - 0.10 * comp_results - 0.15 * comp_reviews + 0.25) / 1.1
    score = round(clamp(score, 0, 100), 1)

    return {
        "score": score,
        "total_results": total_results,
        "analyzed": len(products),
        "median_bsr": med_bsr,
        "est_sales_day_top": round(sum(sales), 1),
        "est_sales_day_median": round(median(sales), 2) if sales else 0,
        "sellers_in_top": sellers,
        "weak_sellers": weak_sellers,
        "median_reviews": med_reviews,
        "median_price": round(median(prices), 2) if prices else None,
        "indie_share": round(indie_share, 2),
        "keyword_hits": keyword_hits,
        "verdict": verdict(score, weak_sellers, demand),
    }


def verdict(score, weak, demand) -> str:
    if demand < 0.2:
        return "brak popytu"
    if score >= 65 and weak >= 2:
        return "dobra nisza"
    if score >= 50:
        return "do sprawdzenia"
    return "nasycona"
