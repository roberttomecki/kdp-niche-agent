"""Odkrywanie fraz z podpowiedzi wyszukiwarki Amazon (tzw. alphabet soup)."""
import json
import string
from collections import defaultdict

from .http import Fetcher
from .markets import Market

# Modyfikatory typowe dla low-content (doklejane po frazie)
LOW_CONTENT_SUFFIXES = ["for", "for women", "for men", "for kids", "for adults", "for teens",
                        "for seniors", "large print", "notebook", "journal", "planner",
                        "log book", "coloring book", "activity book", "workbook", "2027"]


def parse_suggestions(body: str) -> list[str]:
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        return []
    return [s["value"].strip().lower() for s in data.get("suggestions", [])
            if s.get("type", "KEYWORD") == "KEYWORD" and s.get("value")]


def suggest(f: Fetcher, m: Market, prefix: str, alias: str = "stripbooks") -> list[str]:
    params = {"mid": m.mid, "alias": alias, "prefix": prefix, "limit": 11,
              "suggestion-type": "KEYWORD", "page-type": "Search", "lop": m.lang,
              "site-variant": "desktop", "client-info": "amazon-search-ui"}
    body = f.get_json(m.completion_url, params, m.lang)
    return parse_suggestions(body) if body else []


def expand_seed(f: Fetcher, m: Market, seed: str, deep: bool = False,
                alias: str = "stripbooks") -> dict[str, dict]:
    """Zwraca {fraza: {"hits": ile prefiksów ją pokazało, "best_pos": najlepsza pozycja}}.
    hits to przybliżenie popularności: im częściej fraza wraca, tym częściej ją wpisują."""
    seed = seed.strip().lower()
    prefixes = [seed, seed + " "]
    prefixes += [f"{seed} {c}" for c in string.ascii_lowercase + string.digits]
    prefixes += [f"{seed} {s}" for s in LOW_CONTENT_SUFFIXES]
    prefixes += [f"{c} {seed}" for c in string.ascii_lowercase]  # frazy z czymś przed seedem

    found: dict[str, dict] = defaultdict(lambda: {"hits": 0, "best_pos": 99})
    for p in prefixes:
        for pos, s in enumerate(suggest(f, m, p, alias), 1):
            found[s]["hits"] += 1
            found[s]["best_pos"] = min(found[s]["best_pos"], pos)

    if deep:  # drugi poziom: rozwiń najlepsze 2-wyrazowe ogony
        top = sorted(found, key=lambda k: -found[k]["hits"])[:15]
        for kw in top:
            if kw == seed:
                continue
            for c in string.ascii_lowercase:
                for pos, s in enumerate(suggest(f, m, f"{kw} {c}", alias), 1):
                    found[s]["hits"] += 1
                    found[s]["best_pos"] = min(found[s]["best_pos"], pos)
    return dict(found)
