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
import sys
import time
from pathlib import Path

from kdp import llm
from kdp.analyze import analyze_keyword
from kdp.db import DB
from kdp.discover import expand_seed
from kdp.http import Blocked, Fetcher
from kdp.markets import get_market
from kdp.report import write_csv, write_html, write_json, write_keywords_csv

log = logging.getLogger("kdp")
ROOT = Path(__file__).resolve().parent


def load_seeds(args) -> list[str]:
    seeds = list(args.seed or [])
    if args.seeds:
        seeds += [l.strip() for l in Path(args.seeds).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
    return list(dict.fromkeys(s.lower() for s in seeds))


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
    m = get_market(market)
    for i, (kw, _seed, hits, _pos) in enumerate(keywords, 1):
        try:
            r = analyze_keyword(f, db, m, kw, hits=hits, top_n=top_n)
        except Blocked as e:
            log.error(str(e)); return False
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
    log.info("Raport: %s.html", base)
    return niches, keywords


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

    r = sub.add_parser("report", help="wygeneruj raport"); common(r, seeds=False)
    r.add_argument("--ai", action="store_true", help="dodaj wnioski Claude (ANTHROPIC_API_KEY)")

    run = sub.add_parser("run", help="pełny cykl: discover -> analyze -> AI -> report"); common(run)
    run.add_argument("--top", type=int, default=30)
    run.add_argument("--per-keyword", type=int, default=10)
    run.add_argument("--rounds", type=int, default=1, help="rundy z nowymi seedami od Claude")
    run.add_argument("--deep", action="store_true")
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
                if not do_analyze(f, db, market, pick_keywords(db, market, args.top, seeds), args.per_keyword):
                    break
                if use_ai:
                    advice, new = llm.advise(market, db.latest_niches(market), db.keywords(market))
                    seeds = [s for s in new if not db.keywords(market, seed=s)]
                    if not seeds:
                        break
            do_report(db, market, out, advice)


if __name__ == "__main__":
    main()
