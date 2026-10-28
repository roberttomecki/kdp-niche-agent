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
        assert r["analyzed"] == 3 and r["sponsored_count"] == 1 and r["median_bsr"] == 48213
        niches = db.latest_niches("us")
        assert niches[0]["keyword"] == "gratitude journal for women"
        out = Path(d) / "r.html"; write_html(out, "us", niches, [("a b", "a", 3, 1)], "## test")
        assert "gratitude journal for women" in out.read_text()
        print(json.dumps({k: v for k, v in r.items() if k != "top_products"}, indent=1))
