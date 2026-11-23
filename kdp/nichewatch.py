"""Codzienna obserwacja kilku wybranych nisz (plik nisze.txt).

Każdego dnia: świeża strona wyników dla frazy + świeże strony top 10 książek -> historia BSR.
Spadek BSR o ≥20% dzień do dnia (albo pojawienie się BSR) = sygnał sprzedaży.
Po 1–2 tygodniach widać, czy książki w niszy sprzedają się regularnie, czy to był jednorazowy skok.
"""
import logging
import time
from pathlib import Path

from .analyze import analyze_keyword
from .http import Blocked
from .markets import get_market

log = logging.getLogger("kdp")
SALE_DROP = 0.8           # BSR spadł do ≤80% poprzedniego pomiaru → ktoś kupił


def load_niche_watch(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            out.append(line)
    return list(dict.fromkeys(out))


def add_niche(path: Path, kw: str) -> str:
    kw = " ".join(kw.lower().split())
    if not kw:
        return "Użycie: /obserwuj fraza, np. /obserwuj golf log book"
    if kw in load_niche_watch(path):
        return f"„{kw}” już jest obserwowana."
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + kw + "\n", encoding="utf-8")
    return f"Dodane: „{kw}”. Od jutra sprawdzam ją codziennie (wyniki: /nisze)."


def remove_niche(path: Path, kw: str) -> str:
    kw = " ".join(kw.lower().split())
    items = load_niche_watch(path)
    if kw not in items:
        return f"Nie obserwuję „{kw}”."
    path.write_text("".join(k + "\n" for k in items if k != kw), encoding="utf-8")
    return f"Usunięte: „{kw}”."


def watch_niches(f, db, market: str, path: Path) -> int:
    """Pobierz dziś wyniki i strony książek dla obserwowanych fraz (raz na dobę)."""
    m = get_market(market)
    done = 0
    for kw in load_niche_watch(path):
        try:
            res = analyze_keyword(f, db, m, kw, top_n=10, product_ttl_h=18, serp_ttl_h=18)
        except Blocked as e:
            log.error("Obserwacja nisz przerwana: %s", e)
            break
        if res:
            done += 1
            log.info("[%s] nisza „%s”: ocena %.1f", m.code, kw, res["score"])
    return done


def sale_signals(rows) -> tuple[int, int]:
    """(liczba sygnałów sprzedaży, liczba porównań dzień do dnia) z historii jednej książki."""
    sig = comps = 0
    for (_, prev, *_), (_, now, *_) in zip(rows, rows[1:]):
        comps += 1
        if now and (not prev or now <= prev * SALE_DROP):
            sig += 1
    return sig, comps


def niche_trends(db, market: str, path: Path, days: int = 14) -> str:
    since = time.time() - days * 86400
    niches = {n["keyword"]: n for n in db.latest_niches(market)}
    out = []
    for kw in load_niche_watch(path):
        n = niches.get(kw)
        if not n:
            out.append(f"• {kw}: brak danych – pierwszy pomiar przy najbliższym sprawdzeniu")
            continue
        books = sel = total_sig = 0
        max_days = 0
        lines = []
        for p in n.get("top_products", []):
            rows = [r for r in db.product_history(market, p["asin"]) if r[0] >= since]
            if not rows:
                continue
            books += 1
            sig, comps = sale_signals(rows)
            max_days = max(max_days, comps)
            total_sig += sig
            if sig:
                sel += 1
            if sig and (p.get("reviews") or 0) <= 10:
                lines.append(f"    słaba ({p.get('reviews') or 0} op.) sprzedaje: {sig}× – {(p.get('title') or '')[:38]}")
        out.append(f"• {kw}: {sel}/{books} książek sprzedało coś, razem {total_sig} sygnałów sprzedaży "
                   f"w {max_days} dni porównań")
        out += lines[:3]
    if not out:
        return "Nie obserwuję żadnych nisz. Dodaj: /obserwuj fraza"
    return (f"Obserwowane nisze (ostatnie {days} dni; sygnał = BSR spadł o ≥20% dzień do dnia):\n"
            + "\n".join(out))
