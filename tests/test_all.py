import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kdp.parse import parse_serp, parse_product, to_price
from kdp.discover import parse_suggestions, expand_seed
from kdp.score import sales_per_day, score_niche
from kdp.db import DB
from kdp.markets import get_market
from kdp import analyze
from kdp.report import write_html

FX = Path(__file__).parent / "fixtures"

def test_serp():
    r = parse_serp((FX / "serp.html").read_text())
    assert r["total_results"] == 3000
    assert [i["asin"] for i in r["items"]][:2] == ["B0SPONS001", "B0AAAA0001"]
    assert r["items"][0]["sponsored"] and not r["items"][1]["sponsored"]
    assert r["items"][1]["reviews"] == 12345 and r["items"][1]["price"] == 7.99
    assert r["items"][1]["rating"] == 4.7
    assert r["items"][3]["reviews"] == 0

def test_product():
    p = parse_product((FX / "product_us.html").read_text())
    assert p["bsr"] == 48213 and p["pages"] == 120 and p["indie"] and p["reviews"] == 23
    assert "2025" in p["pub_date"]
    d = parse_product((FX / "product_de.html").read_text())
    assert d["bsr"] == 12345 and d["reviews"] == 1204 and d["pages"] == 110

def test_price():
    assert to_price("6,99 €") == 6.99 and to_price("$1,234.50") == 1234.5 and to_price("1.234,50 €") == 1234.5

def test_sales_curve():
    assert 3.5 < sales_per_day(50_000) < 4.5
    assert sales_per_day(10) > sales_per_day(1000) > sales_per_day(1_000_000) > 0
    assert sales_per_day(None) == 0

def test_score_orders_niches():
    easy = [{"bsr": 40_000, "reviews": 10, "price": 7, "indie": True}] * 6 + [{"bsr": 900_000, "reviews": 5}] * 4
    hard = [{"bsr": 2_000, "reviews": 5000, "price": 7}] * 10
    dead = [{"bsr": 4_000_000, "reviews": 2}] * 10
    se, sh, sd = (score_niche(x, t, 1.0, 5) for x, t in [(easy, 800), (hard, 60000), (dead, 300)])
    assert se["score"] > sh["score"] and se["verdict"] == "dobra nisza"
    assert sd["verdict"] == "brak popytu"

class FakeFetcher:
    debug_dir = None
    def get_json(self, url, params, lang, ttl_h=72):
        return (FX / "suggest.json").read_text()
    def get_html(self, url, lang, ttl_h=72):
        return (FX / ("serp.html" if "/s?" in url else "product_us.html")).read_text()

def test_pipeline():
    m = get_market("us")
    found = expand_seed(FakeFetcher(), m, "gratitude journal")
    assert parse_suggestions((FX / "suggest.json").read_text()) == ["gratitude journal for women", "gratitude journal for kids"]
    assert found["gratitude journal for women"]["hits"] > 10
    with tempfile.TemporaryDirectory() as d:
        db = DB(Path(d) / "t.sqlite")
        r = analyze.analyze_keyword(FakeFetcher(), db, m, "gratitude journal for women", hits=20, top_n=10)
        assert r["analyzed"] == 6 and r["sponsored_count"] == 1 and r["median_bsr"] == 48213
        niches = db.latest_niches("us")
        assert niches[0]["keyword"] == "gratitude journal for women"
        out = Path(d) / "r.html"; write_html(out, "us", niches, [("a b", "a", 3, 1)], "## test")
        assert "gratitude journal for women" in out.read_text()
        print(json.dumps({k: v for k, v in r.items() if k != "top_products"}, indent=1))

def test_total_results_ignores_numbers_in_query():
    from bs4 import BeautifulSoup
    from kdp.parse import parse_total_results
    h = '<span data-component-type="s-result-info-bar"><span>1-16 of 612 results for</span> <span>"sudoku large print 2027"</span></span>'
    assert parse_total_results(BeautifulSoup(h, "html.parser")) == 612
    h = '<span data-component-type="s-result-info-bar"><span>1-48 von über 3.000 Ergebnissen für</span> <span>„kalender 2027“</span></span>'
    assert parse_total_results(BeautifulSoup(h, "html.parser")) == 3000

def test_bought_badge():
    from kdp.parse import parse_bought
    assert parse_bought("Large Print 4.6 out of 5 stars 1,234 50+ bought in past month $9.99") == 50
    assert parse_bought("1K+ bought in past month") == 1000
    assert parse_bought("Mehr als 100 Mal im letzten Monat gekauft") == 100
    assert parse_bought("Plus de 50 achetés au cours du mois dernier") == 50
    assert parse_bought("No badge here, 2027 edition") is None

def test_badge_in_serp_and_history():
    html = (FX / "serp.html").read_text().replace(
        "<span>23</span></a>", "<span>23</span></a><span>200+ bought in past month</span>")
    r = parse_serp(html)
    assert [i["bought_month"] for i in r["items"]][:4] == [None, None, 200, None]
    assert r["items"][-1]["is_book"] is False and r["items"][1]["is_book"] is True
    class F(FakeFetcher):
        def get_html(self, url, lang, ttl_h=72):
            return html if "/s?" in url else (FX / "product_us.html").read_text()
    with tempfile.TemporaryDirectory() as d:
        db = DB(Path(d) / "t.sqlite")
        res = analyze.analyze_keyword(F(), db, get_market("us"), "gratitude journal for women", hits=5)
        assert res["bought_month_top"] == 200 and res["with_badge"] == 1
        h = db.product_history("us", "B0BBBB0002")
        assert len(h) == 1 and h[0][4] == 200
        analyze.analyze_keyword(F(), db, get_market("us"), "gratitude journal for kids", hits=5)
        assert len(db.product_history("us", "B0BBBB0002")) == 1  # max 1 wpis na dobę

def test_screen_and_rotation():
    from kdp.screen import screen_score, screen_keywords, latest_screens
    hot = [{"sponsored": False, "reviews": 12, "bought_month": 200}] * 4 + [{"sponsored": False, "reviews": 900}] * 6
    cold = [{"sponsored": False, "reviews": 3000}] * 10
    assert screen_score(hot, 2000, 10)["score"] > screen_score(cold, 60000, 10)["score"]
    with tempfile.TemporaryDirectory() as d:
        db = DB(Path(d) / "s.sqlite")
        ranked = screen_keywords(FakeFetcher(), db, get_market("us"), [("a b", "a", 3, 1), ("c d", "c", 9, 1)])
        assert len(ranked) == 2 and latest_screens(db, "us")[0][0] in ("a b", "c d")
    import types, kdp_agent
    p = Path(d if False else tempfile.mkdtemp()) / "seeds.txt"
    p.write_text("\n".join(f"s{i}" for i in range(25)))
    a = types.SimpleNamespace(seed=None, seeds=str(p), rotate=10)
    got = kdp_agent.load_seeds(a)
    assert len(got) == 10 and len(set(got)) == 10

def test_non_book_results_skipped():
    from kdp.screen import screen_score
    mats = [{"sponsored": False, "reviews": 0, "bought_month": 1000, "is_book": False}] * 10
    assert screen_score(mats, 11, 5)["score"] == 0.0

def test_stale_non_book_niche_removed():
    from kdp.screen import screen_keywords
    html = '<div data-component-type="s-search-result" data-asin="B0X"><h2>Desk mat</h2></div>' * 6
    class F(FakeFetcher):
        def get_html(self, url, lang, ttl_h=72):
            return html
    with tempfile.TemporaryDirectory() as d:
        db = DB(Path(d) / "x.sqlite")
        db.save_niche("us", "coin desk mat", 99, {"verdict": "x"}); db.commit()
        screen_keywords(F(), db, get_market("us"), [("coin desk mat", "coin", 1, 1)])
        assert db.latest_niches("us") == []

def test_tiny_result_sets_penalised():
    from kdp.screen import screen_score
    items = [{"sponsored": False, "reviews": 2, "bought_month": None, "is_book": True}] * 10
    assert screen_score(items, 7, 5)["score"] < screen_score(items, 3000, 5)["score"] / 2

def test_deep_score_tiny_results():
    p = [{"bsr": 40_000, "reviews": 3, "price": 9, "indie": True}] * 8
    r = score_niche(p, 13, 1.0, 5)
    assert r["verdict"] == "za mało wyników" and r["score"] < score_niche(p, 5000, 1.0, 5)["score"]

def test_watchlist_tracking():
    import kdp_agent
    with tempfile.TemporaryDirectory() as d:
        w = Path(d) / "watch.txt"; w.write_text("# x\nb0bbbb0002 Moja książka\n")
        assert kdp_agent.load_watchlist(w) == [("B0BBBB0002", "Moja książka")]
        db = DB(Path(d) / "w.sqlite")
        kdp_agent.track_watchlist(FakeFetcher(), db, "us", w)
        h = db.product_history("us", "B0BBBB0002")
        assert len(h) == 1 and h[0][1] == 48213

def test_book_events():
    from kdp.notify import book_events
    assert "pierwsza sprzedaż" in book_events("PLB", "B0X", (0, None, 0, None, None, ""), {"bsr": 812345, "reviews": 0})[0]
    assert "kolejna" in book_events("PLB", "B0X", (0, 800000, 0, None, None, ""), {"bsr": 90000, "reviews": 0})[0]
    assert "opinia" in book_events("PLB", "B0X", (0, 90000, 0, None, None, ""), {"bsr": 95000, "reviews": 1})[0]
    assert book_events("PLB", "B0X", (0, 90000, 1, None, None, ""), {"bsr": 95000, "reviews": 1}) == []

def test_bot_commands():
    from kdp.bot import Bot
    from kdp.watch import add_to_watchlist
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); w = root / "watch.txt"; w.write_text("B0BBBB0002 Moja książka")
        assert "nie wygląda" in add_to_watchlist(w, "abc", "x")
        assert "Dodane" in add_to_watchlist(w, "b0cccc0003", "Mileage Log Book")
        assert "już jest" in add_to_watchlist(w, "B0CCCC0003", "")
        assert w.read_text().splitlines()[-1] == "B0CCCC0003 Mileage Log Book"
        b = Bot(root, root / "db.sqlite", w)
        DB(root / "db.sqlite")
        assert "Komendy" in b.handle("/pomoc")
        assert "Nie znam" in b.handle("/xyz")
        assert "brak danych" in b.handle("/moje@MyBot")
        assert "Brak analizy" in b.handle("/raport")
        b.cmd_sprawdz = lambda a: "ok"; assert b.handle("/sprawdź") == "ok"   # polskie znaki → /sprawdz
        assert b.handle("/Dodaj").startswith("Użycie")
