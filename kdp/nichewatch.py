"""Codzienna obserwacja kilku wybranych nisz.

Dwa źródła fraz:
  nisze.txt        – dopisane ręcznie (/obserwuj), obserwowane na stałe;
  nisze_auto.json  – wybierane automatycznie po każdym poniedziałkowym przebiegu (5 najlepszych z raportu),
                     obserwowane przez AUTO_DAYS dni, potem usuwane z werdyktem wysłanym na Telegram.

Każdego dnia: świeża strona wyników dla frazy + świeże strony top 10 książek -> historia BSR.
Spadek BSR o ≥20% dzień do dnia (albo pojawienie się BSR) = sygnał sprzedaży.
Po 1–2 tygodniach widać, czy książki w niszy sprzedają się regularnie, czy to był jednorazowy skok.
"""
import json
import logging
import time
from pathlib import Path

from . import notify
from .analyze import analyze_keyword
from .http import Blocked
from .markets import get_market
from .score import relevant

log = logging.getLogger("kdp")
SALE_DROP = 0.8           # BSR spadł do ≤80% poprzedniego pomiaru → ktoś kupił
AUTO_PICK = 5             # ile nisz dodać automatycznie co tydzień
AUTO_DAYS = 14            # jak długo obserwować niszę dodaną automatycznie
AUTO_MIN_SCORE = 55
DONE_DAYS = 90            # po zakończonej obserwacji nie wybieraj tej niszy ponownie przez 90 dni


def _auto_path(path: Path) -> Path:
    return path.with_name(path.stem + "_auto.json")


def load_auto(path: Path) -> dict[str, float]:
    try:
        return json.loads(_auto_path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def save_auto(path: Path, auto: dict[str, float]):
    _auto_path(path).write_text(json.dumps(auto, ensure_ascii=False, indent=1), encoding="utf-8")


def _done_path(path: Path) -> Path:
    return path.with_name(path.stem + "_done.json")


def load_done(path: Path) -> dict[str, float]:
    """Nisze, których automatyczna obserwacja już się skończyła (nie wybieramy ich ponownie przez DONE_DAYS)."""
    try:
        return json.loads(_done_path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def load_manual(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            out.append(line)
    return list(dict.fromkeys(out))


def load_niche_watch(path: Path) -> list[str]:
    """Wszystkie obserwowane frazy: ręczne + automatyczne."""
    return list(dict.fromkeys(load_manual(path) + list(load_auto(path))))


def add_niche(path: Path, kw: str) -> str:
    kw = " ".join(kw.lower().split())
    if not kw:
        return "Użycie: /obserwuj fraza, np. /obserwuj golf log book"
    if kw in load_manual(path):
        return f"„{kw}” już jest obserwowana."
    auto = load_auto(path)
    if auto.pop(kw, None) is not None:       # z automatycznej → na stałe
        save_auto(path, auto)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + kw + "\n", encoding="utf-8")
    return f"Dodane: „{kw}”. Od jutra sprawdzam ją codziennie (wyniki: /nisze)."


def remove_niche(path: Path, kw: str) -> str:
    kw = " ".join(kw.lower().split())
    auto = load_auto(path)
    if kw in auto:
        auto.pop(kw)
        save_auto(path, auto)
        return f"Usunięte: „{kw}”."
    items = load_manual(path)
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


def niche_stats(db, market: str, niche: dict, since: float) -> dict:
    books = sel = total_sig = max_days = 0
    weak = []
    for p in niche.get("top_products", []):
        rows = [r for r in db.product_history(market, p["asin"]) if r[0] >= since]
        if not rows:
            continue
        books += 1
        sig, comps = sale_signals(rows)
        max_days = max(max_days, comps)
        total_sig += sig
        if sig:
            sel += 1
            if (p.get("reviews") or 0) <= 10:
                weak.append((sig, p.get("reviews") or 0, (p.get("title") or "")[:38]))
    return dict(books=books, selling=sel, signals=total_sig, days=max_days, weak=weak)


def verdict(st: dict) -> str:
    if st["days"] < 3:
        return "⏳ za mało danych"
    if st["selling"] >= 5 or (st["selling"] >= 3 and len(st["weak"]) >= 2):
        return "✅ sprzedaje się regularnie"
    if st["selling"] >= 2:
        return "⚠️ średnio"
    return "❌ słaba sprzedaż"


def _line(kw, st, tag=""):
    out = [f"• {kw}{tag}: {verdict(st)} – {st['selling']}/{st['books']} książek sprzedało, "
           f"{st['signals']} sygnałów w {st['days']} dni"]
    for sig, rev, title in sorted(st["weak"], reverse=True)[:3]:
        out.append(f"    słaba ({rev} op.) sprzedaje: {sig}× – {title}")
    return out


def niche_trends(db, market: str, path: Path, days: int = 14) -> str:
    since = time.time() - days * 86400
    niches = {n["keyword"]: n for n in db.latest_niches(market)}
    auto = load_auto(path)
    out = []
    for kw in load_niche_watch(path):
        tag = ""
        if kw in auto:
            tag = " (auto do " + time.strftime("%d.%m", time.localtime(auto[kw] + AUTO_DAYS * 86400)) + ")"
        n = niches.get(kw)
        if not n:
            out.append(f"• {kw}{tag}: brak danych – pierwszy pomiar przy najbliższym sprawdzeniu")
            continue
        out += _line(kw, niche_stats(db, market, n, since), tag)
    if not out:
        return "Nie obserwuję żadnych nisz. Dodaj: /obserwuj fraza"
    return (f"Obserwowane nisze (ostatnie {days} dni; sygnał = BSR spadł o ≥20% dzień do dnia):\n"
            + "\n".join(out))


def own_labels(watch: Path) -> list[str]:
    from .watch import load_watchlist
    return [label.lower() for _, label in load_watchlist(watch) if label]


def pick_candidates(db, market: str, path: Path, watch: Path, n: int = AUTO_PICK,
                    max_age_days: float = 8) -> list[str]:
    """Najlepsze świeże nisze z raportu, bez już obserwowanych i bez nisz Twoich książek."""
    recent_done = {k for k, t in load_done(path).items() if time.time() - t < DONE_DAYS * 86400}
    watched = set(load_niche_watch(path)) | recent_done
    labels = own_labels(watch)
    from .watch import load_watchlist
    own_asins = {a for a, _ in load_watchlist(watch)}
    cutoff = time.time() - max_age_days * 86400
    picked = []
    for niche in db.latest_niches(market):                    # posortowane po ocenie malejąco
        kw = niche["keyword"]
        if kw in watched or niche["score"] < AUTO_MIN_SCORE:
            continue
        if niche.get("verdict") not in ("dobra nisza", "do sprawdzenia"):
            continue
        if time.mktime(time.strptime(niche["analyzed_at"], "%Y-%m-%d")) < cutoff:
            continue
        tops = niche.get("top_products", [])
        if any(p.get("asin") in own_asins for p in tops):
            continue
        if any(relevant(label, kw) for label in labels):    # ta sama tematyka co Twoja książka
            continue
        if tops and sum(relevant(p.get("title"), kw) for p in tops) < len(tops) / 2:
            continue                                          # w wynikach głównie coś innego niż fraza
        if any(relevant(kw, other) and relevant(other, kw) for other in picked + list(watched)):
            continue                                          # nie bierz wariantów fraz już wybranych/obserwowanych
        picked.append(kw)
        if len(picked) >= n:
            break
    return picked


def weekly_rotation(db, market: str, path: Path, watch: Path) -> str:
    """Po poniedziałkowym przebiegu: zakończ obserwacje po AUTO_DAYS dniach (werdykt) i dodaj nowe."""
    now = time.time()
    auto = load_auto(path)
    niches = {x["keyword"]: x for x in db.latest_niches(market)}
    done = [kw for kw, ts in auto.items() if now - ts >= (AUTO_DAYS - 0.5) * 86400]
    msg = []
    if done:
        msg.append(f"🏁 Koniec {AUTO_DAYS}-dniowej obserwacji:")
        for kw in done:
            n = niches.get(kw)
            if n:
                msg += _line(kw, niche_stats(db, market, n, auto[kw] - 3600))
            auto.pop(kw)
        msg.append("Żeby obserwować dalej na stałe: /obserwuj fraza")
        hist = load_done(path)
        hist.update({kw: now for kw in done})
        _done_path(path).write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    save_auto(path, auto)
    new = pick_candidates(db, market, path, watch)
    for kw in new:
        auto[kw] = now
    save_auto(path, auto)
    if new:
        msg.append(f"🔭 Nowe nisze do obserwacji przez {AUTO_DAYS} dni:")
        msg += [f"• {kw} (ocena {niches[kw]['score']:.0f})" for kw in new]
        msg.append("Postęp: /nisze  •  usuń: /przestan fraza")
    text = "\n".join(msg)
    if text:
        log.info("Rotacja nisz:\n%s", text)
        if notify.configured():
            notify.send(text)
    return text
