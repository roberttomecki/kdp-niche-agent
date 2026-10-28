"""Opcjonalna warstwa „agenta” – Claude analizuje wyniki i proponuje kolejne nisze.

Wymaga: pip install anthropic oraz ANTHROPIC_API_KEY. Model: KDP_MODEL
(domyślnie claude-sonnet-5-5).
"""
import json
import os
import re

PROMPT = """Jesteś analitykiem rynku Amazon KDP, specjalizujesz się w książkach low-content
(notesy, planery, dzienniki, kolorowanki, łamigłówki, logbooki). Rynek: {market}.

Poniżej dane z narzędzia: frazy z autocomplete Amazona (hits = jak często fraza wracała
w podpowiedziach, przybliżenie popularności) i analiza konkurencji top wyników
(BSR, szacowana sprzedaż/dzień, opinie, ceny, weak_sellers = książki z <50 opiniami,
które mimo to sprzedają ≥0,5 szt./dzień – najważniejszy sygnał „da się wejść”).

DANE:
{data}

Zadania (odpowiedz po polsku, w Markdown):
1. Pogrupuj frazy w nisze/podnisze (klastry tematyczne). Dla każdej najlepszej niszy podaj:
   uzasadnienie liczbami z danych, główne ryzyko, kąt wyróżnienia (odbiorca, format, styl).
2. Dla 3 najlepszych nisz zaproponuj: tytuł + podtytuł oraz 7 pól słów kluczowych KDP
   (backend keywords, każde pole to fraza, bez powtarzania słów z tytułu).
3. Wskaż nisze, których unikać, i dlaczego.
4. Na końcu podaj blok ```json {{"next_seeds": [...]}} ``` z 5-10 NOWYMI frazami bazowymi
   (po angielsku dla rynków anglojęzycznych, w języku rynku dla pozostałych), wartymi
   zbadania w następnej rundzie – sąsiednie lub węższe nisze.
Nie wymyślaj liczb, których nie ma w danych."""


def available() -> bool:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def compact(niches: list[dict], keywords: list[tuple], limit=40) -> str:
    rows = []
    for n in niches[:limit]:
        rows.append({k: n.get(k) for k in ("keyword", "score", "verdict", "total_results",
                     "median_bsr", "est_sales_day_top", "sellers_in_top", "weak_sellers",
                     "median_reviews", "median_price", "indie_share", "keyword_hits")})
    analyzed = {n["keyword"] for n in niches}
    extra = [{"keyword": k, "hits": h} for k, _, h, _ in keywords if k not in analyzed][:80]
    return json.dumps({"analyzed_niches": rows, "other_keywords_from_autocomplete": extra},
                      ensure_ascii=False)


def advise(market: str, niches: list[dict], keywords: list[tuple]) -> tuple[str, list[str]]:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("KDP_MODEL", "claude-sonnet-5-5"),
        max_tokens=6000,
        messages=[{"role": "user", "content": PROMPT.format(
            market=market, data=compact(niches, keywords))}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    seeds = []
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            seeds = [s.strip().lower() for s in json.loads(m.group(1)).get("next_seeds", []) if s.strip()]
        except ValueError:
            pass
    return text, seeds
