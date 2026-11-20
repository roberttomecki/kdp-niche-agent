#!/usr/bin/env python3
"""Agent do szukania nisz Amazon KDP (low-content).

Przykłady:
  python kdp_agent.py run --seeds seeds.txt --market us --rounds 2
  python kdp_agent.py discover --seed "gratitude journal" --market us de
  python kdp_agent.py analyze --market us --top 40
  python kdp_agent.py report --market us
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

from kdp import llm
from kdp.analyze import analyze_keyword
from kdp.db import DB
from kdp.discover import expand_seed
from kdp.http import Blocked, Fetcher
from kdp.markets import get_market
from kdp.screen import latest_screens, screen_keywords
from kdp.report import write_csv, write_html, write_json, write_keywords_csv

log = logging.getLogger("kdp")
ROOT = Path(__file__).resolve().parent


def load_seeds(args) -> list[str]:
    seeds = list(args.seed or [])
    if args.seeds:
        seeds += [l.strip() for l in Path(args.seeds).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
    seeds = list(dict.fromkeys(s.lower() for s in seeds))
    n = getattr(args, "rotate", 0) or 0
    if n and len(seeds) > n:
        # co tydzień inna porcja listy: tydzień ISO wyznacza początek okna
        week = int(time.strftime("%V")) + 53 * int(time.strftime("%G"))
        start = (week * n) % len(seeds)
        seeds = (seeds + seeds)[start:start + n]
        log.info("Rotacja: w tym tygodniu %d z listy seedów (od pozycji %d)", n, start + 1)
    return seeds


def do_discover(f, db, market, seeds, deep):
    m = get_market(market)
    total = 0
    for s in seeds:
        found = expand_seed(f, m, s, deep=deep)
        for kw, v in found.items():
            db.upsert_keyword(m.code, kw, s, v["hits"], v["best_pos"])
        db.commit()
        total += len(found)
        log.info("[%s] '%s': %d fraz", m.code, s, len(found))
    return total


def pick_keywords(db, market, top, seeds=None, min_words=2):
    rows = []
    for s in (seeds or [None]):
        rows += db.keywords(market, seed=s)
    rows = [r for r in rows if len(r[0].split()) >= min_words]
    rows.sort(key=lambda r: (-r[2], r[3]))
    seen, out = set(), []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0]); out.append(r)
    return out[:top]


def do_analyze(f, db, market, keywords, top_n):
    """Przy blokadzie Amazona robi przerwę (KDP_BLOCK_PAUSE s, domyślnie 20 min) i ponawia tę samą
    frazę; po KDP_MAX_PAUSES przerwach (domyślnie 3) kończy, zachowując to, co już zebrał."""
    m = get_market(market)
    pause = int(os.getenv("KDP_BLOCK_PAUSE", "1200"))
    max_pauses = int(os.getenv("KDP_MAX_PAUSES", "3"))
    pauses = 0
    for i, (kw, _seed, hits, _pos) in enumerate(keywords, 1):
        while True:
            try:
                r = analyze_keyword(f, db, m, kw, hits=hits, top_n=top_n)
                break
            except Blocked as e:
                if pauses >= max_pauses:
                    log.error("%s Przerywam po %d przerwach (%d/%d fraz).", e, pauses, i - 1, len(keywords))
                    return False
                pauses += 1
                log.warning("[%s] Blokada Amazona przy '%s' – przerwa %d min (%d/%d), potem ponawiam.",
                            m.code, kw, pause // 60, pauses, max_pauses)
                time.sleep(pause)
                f.blocked_count = 0
        if r:
            log.info("[%s] %d/%d %-45s ocena %5.1f  %s", m.code, i, len(keywords), kw[:45], r["score"], r["verdict"])
    return True


def do_report(db, market, out_dir: Path, advice=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    niches = db.latest_niches(market)
    keywords = db.keywords(market)
    stamp = time.strftime("%Y%m%d_%H%M")
    base = out_dir / f"kdp_{market}_{stamp}"
    write_csv(base.with_suffix(".csv"), niches)
    write_keywords_csv(out_dir / f"kdp_{market}_{stamp}_keywords.csv", keywords)
    write_json(base.with_suffix(".json"), niches)
    write_html(base.with_suffix(".html"), market, niches, keywords, advice)
    if advice:
        base.with_suffix(".md").write_text(advice, encoding="utf-8")
    # stała nazwa najnowszego raportu – łatwo ją pobrać (scp …/reports/latest_<rynek>.html)
    import shutil
    shutil.copyfile(base.with_suffix(".html"), out_dir / f"latest_{market}.html")
    log.info("Raport: %s.html (kopia: latest_%s.html)", base, market)
    return niches, keywords


def show_history(db, market, keyword=None, asins=None):
    asins = list(asins or [])
    if keyword:
        for n in db.latest_niches(market):
            if n["keyword"] == keyword.lower():
                asins += [p["asin"] for p in n.get("top_products", [])]
        if not asins:
            sys.exit(f"Brak frazy '{keyword}' w bazie dla rynku {market}.")
    if not asins:
        sys.exit("Podaj --keyword albo --asin")
    for a in dict.fromkeys(asins):
        rows = db.product_history(market, a)
        if not rows:
            continue
        print(f"\n{a}  {rows[-1][5][:70]}")
        print(f"  {'data':10} {'BSR':>9} {'opinie':>7} {'cena':>6} {'kupione/mies.':>14}")
        for ts, bsr, rev, price, bought, _ in rows:
            print(f"  {time.strftime('%Y-%m-%d', time.localtime(ts)):10} {bsr or '-':>9} {rev if rev is not None else '-':>7} "
                  f"{price or '-':>6} {(str(bought) + '+') if bought else '-':>14}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(ROOT / "data" / "kdp.sqlite"))
    p.add_argument("--out", default=str(ROOT / "reports"))
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, seeds=True):
        sp.add_argument("--market", nargs="+", default=["us"], help="us uk de fr it es ca au")
        if seeds:
            sp.add_argument("--seed", action="append", help="fraza bazowa (można wiele razy)")
            sp.add_argument("--seeds", help="plik z frazami bazowymi, jedna na linię")

    d = sub.add_parser("discover", help="zbierz frazy z autocomplete"); common(d)
    d.add_argument("--deep", action="store_true", help="drugi poziom rozwijania (więcej zapytań)")

    a = sub.add_parser("analyze", help="przeanalizuj konkurencję dla zebranych fraz"); common(a)
    a.add_argument("--top", type=int, default=30, help="ile fraz analizować")
    a.add_argument("--per-keyword", type=int, default=10, help="ile książek z topu sprawdzać")

    h = sub.add_parser("history", help="historia BSR/opinii/odznak książek dla frazy lub ASIN")
    common(h, seeds=False)
    h.add_argument("--keyword", help="fraza z raportu – pokaże książki z jej topu")
    h.add_argument("--asin", action="append", help="konkretny ASIN (można wiele razy)")

    sc = sub.add_parser("screens", help="najlepsze frazy z ostatniego przesiewu"); common(sc, seeds=False)
    sc.add_argument("--limit", type=int, default=30)

    r = sub.add_parser("report", help="wygeneruj raport"); common(r, seeds=False)
    r.add_argument("--ai", action="store_true", help="dodaj wnioski Claude (ANTHROPIC_API_KEY)")

    run = sub.add_parser("run", help="pełny cykl: discover -> analyze -> AI -> report"); common(run)
    run.add_argument("--top", type=int, default=30)
    run.add_argument("--per-keyword", type=int, default=10)
    run.add_argument("--rounds", type=int, default=1, help="rundy z nowymi seedami od Claude")
    run.add_argument("--deep", action="store_true")
    run.add_argument("--screen", type=int, default=0,
                     help="przesiej najpierw tyle fraz (1 strona wyników na frazę), "
                          "a pełną analizę zrób dla --top najlepszych z przesiewu")
    run.add_argument("--rotate", type=int, default=0,
                     help="użyj tylko tylu seedów z listy, co tydzień innych")
    run.add_argument("--no-ai", action="store_true")

    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    db = DB(Path(args.db))
    f = Fetcher(db, debug_dir=ROOT / "debug")
    out = Path(args.out)

    for market in args.market:
        get_market(market)
        if args.cmd == "discover":
            n = do_discover(f, db, market, load_seeds(args) or sys.exit("Podaj --seed lub --seeds"), args.deep)
            log.info("[%s] zebrano łącznie %d fraz", market, n)
        elif args.cmd == "analyze":
            seeds = load_seeds(args) or None
            do_analyze(f, db, market, pick_keywords(db, market, args.top, seeds), args.per_keyword)
        elif args.cmd == "screens":
            rows = latest_screens(db, market, args.limit)
            print(f"{'fraza':42} {'przesiew':>8} {'kup/mies':>9} {'słabe':>6} {'słabe+odzn.':>11} {'opinie':>7} {'wyniki':>8}  data")
            for k, s, d, t in rows:
                print(f"{k[:42]:42} {s:8.1f} {d['badges_sum']:9} {d['low_review_books']:6} {d['low_with_badge']:11} "
                      f"{d['median_reviews']:7.0f} {d['total_results'] or '-':>8}  {time.strftime('%Y-%m-%d', time.localtime(t))}")
        elif args.cmd == "history":
            show_history(db, market, args.keyword, args.asin)
        elif args.cmd == "report":
            advice = None
            if args.ai and llm.available():
                advice, _ = llm.advise(market, db.latest_niches(market), db.keywords(market))
            do_report(db, market, out, advice)
        elif args.cmd == "run":
            seeds = load_seeds(args) or sys.exit("Podaj --seed lub --seeds")
            use_ai = not args.no_ai and llm.available()
            if not args.no_ai and not use_ai:
                log.info("Brak ANTHROPIC_API_KEY lub pakietu anthropic – pomijam warstwę AI.")
            advice = None
            for rnd in range(1, args.rounds + 1):
                log.info("=== [%s] runda %d, seedy: %s", market, rnd, ", ".join(seeds))
                do_discover(f, db, market, seeds, args.deep)
                chosen = pick_keywords(db, market, args.top, seeds)
                if args.screen:
                    try:
                        ranked = screen_keywords(f, db, get_market(market),
                                                 pick_keywords(db, market, args.screen, seeds))
                    except Blocked as e:
                        log.error("Przesiew przerwany: %s", e); ranked = []
                    if ranked:
                        chosen = [kw for _, kw, _ in ranked[:args.top]]
                        log.info("[%s] przesiew: %d fraz, do pełnej analizy %d (najlepsza: %s, %.1f)",
                                 market, len(ranked), len(chosen), ranked[0][1][0], ranked[0][0])
                if not do_analyze(f, db, market, chosen, args.per_keyword):
                    break
                if not use_ai:
                    break  # bez AI nie ma nowych seedów – kolejna runda nic nie wniesie
                if use_ai:
                    advice, new = llm.advise(market, db.latest_niches(market), db.keywords(market))
                    seeds = [s for s in new if not db.keywords(market, seed=s)]
                    if not seeds:
                        break
            do_report(db, market, out, advice)


if __name__ == "__main__":
    main()
