"""Parsowanie wyników wyszukiwania i stron produktów Amazon.

Amazon często zmienia HTML. Selektory są celowo „luźne”, a gdy coś przestanie
działać, strona trafia do katalogu debug/ – wtedy poprawia się tylko ten plik.
"""
import re

from bs4 import BeautifulSoup

BSR_LABELS = ("Best Sellers Rank", "Bestseller-Rang", "Amazon Bestseller-Rang",
              "Classement des meilleures ventes", "Posizione nella classifica Bestseller",
              "Clasificación en los más vendidos", "Amazon Bestsellers Rank")
PAGES_LABELS = ("Print length", "pages", "Seitenzahl", "Nombre de pages",
                "Lunghezza stampa", "Número de páginas", "Paperback", "Taschenbuch",
                "Broché", "Copertina flessibile", "Tapa blanda")
INDIE_MARKERS = ("Independently published", "Independently Published",
                 "Independent published", "Unabhängig veröffentlicht")


def to_int(text) -> int | None:
    if text is None:
        return None
    digits = re.sub(r"[^\d]", "", str(text))
    return int(digits) if digits else None


def to_price(text) -> float | None:
    if not text:
        return None
    t = re.sub(r"[^\d,.]", "", text)
    if not t:
        return None
    if "," in t and "." in t:  # 1.234,56 albo 1,234.56
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def parse_total_results(soup: BeautifulSoup) -> int | None:
    bar = soup.select_one('[data-component-type="s-result-info-bar"]') or \
        soup.select_one("span[data-component-type='s-result-info-bar']")
    text = bar.get_text(" ", strip=True) if bar else ""
    if not text:
        m = re.search(r"\d[\d.,]*\s*-\s*\d+[^<]{0,40}?(\d[\d.,]{2,})", soup.get_text(" ", strip=True))
        return to_int(m.group(1)) if m else None
    nums = [to_int(n) for n in re.findall(r"\d[\d.,]*", text)]
    nums = [n for n in nums if n]
    return max(nums) if nums else None


def parse_serp(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for pos, card in enumerate(soup.select('div[data-component-type="s-search-result"]'), 1):
        asin = card.get("data-asin")
        if not asin:
            continue
        text = card.get_text(" ", strip=True)
        sponsored = bool(card.select_one(".puis-sponsored-label-text, .s-sponsored-label-text")) \
            or re.search(r"\b(Sponsored|Gesponsert|Sponsorisé|Sponsorizzato|Patrocinado)\b", text[:200]) is not None
        h2 = card.select_one("h2")
        title = h2.get_text(" ", strip=True) if h2 else ""
        price_el = card.select_one(".a-price .a-offscreen")
        reviews = None
        rev_el = card.select_one('a[href*="customerReviews"] span') or \
            card.select_one('[aria-label$="ratings"], [aria-label$="Bewertungen"], [aria-label$="évaluations"]')
        if rev_el:
            reviews = to_int(rev_el.get("aria-label") or rev_el.get_text())
        rating = None
        star = card.select_one('[aria-label*="out of 5"], [aria-label*="von 5"], [aria-label*="sur 5"], .a-icon-alt')
        if star:
            m = re.search(r"(\d[.,]\d)", star.get("aria-label") or star.get_text())
            rating = float(m.group(1).replace(",", ".")) if m else None
        items.append({"pos": pos, "asin": asin, "title": title, "sponsored": sponsored,
                      "price": to_price(price_el.get_text()) if price_el else None,
                      "reviews": reviews or 0, "rating": rating})
    return {"total_results": parse_total_results(soup), "items": items}


def _detail_text(soup: BeautifulSoup) -> str:
    parts = []
    for sel in ("#detailBulletsWrapper_feature_div", "#detailBullets_feature_div",
                "#productDetails_detailBullets_sections1", "#prodDetails",
                "#rich_product_information", "#bookDetails_container_div"):
        el = soup.select_one(sel)
        if el:
            parts.append(el.get_text(" ", strip=True))
    return " ".join(parts) or soup.get_text(" ", strip=True)


def parse_product(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    details = re.sub(r"\s+", " ", _detail_text(soup))
    bsr = None
    for label in BSR_LABELS:
        i = details.find(label)
        if i >= 0:
            m = re.search(r"(?:#|Nr\.|n\.|nº|n°)?\s*(\d[\d.,   ]*\d|\d)", details[i + len(label):i + len(label) + 80])
            bsr = to_int(m.group(1)) if m else None
            break
    pages = None
    m = re.search(r"(\d{2,4})\s*(?:pages|Seiten|páginas|pagine)", details)
    if m:
        pages = int(m.group(1))
    title_el = soup.select_one("#productTitle")
    rev_el = soup.select_one("#acrCustomerReviewText")
    date = None
    m = re.search(r"(?:Publication date|Erscheinungstermin|Date de publication|Data di pubblicazione|Fecha de publicación)\s*[:‏‎ ]*([^:]{6,25}?\d{4})", details)
    if m:
        date = m.group(1).strip(" :‏‎")
    return {
        "title": title_el.get_text(" ", strip=True) if title_el else None,
        "bsr": bsr,
        "reviews": to_int(rev_el.get_text()) if rev_el else None,
        "pages": pages,
        "pub_date": date,
        "indie": any(x in details for x in INDIE_MARKERS),
    }
