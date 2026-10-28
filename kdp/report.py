"""Raporty: CSV (nisze, frazy) i samodzielny plik HTML z sortowaną tabelą."""
import csv
import html
import json
import time
from pathlib import Path

COLS = [("keyword", "Fraza"), ("score", "Ocena"), ("verdict", "Werdykt"),
        ("total_results", "Wyników"), ("median_bsr", "Mediana BSR"),
        ("est_sales_day_top", "Sprz./dzień top"), ("sellers_in_top", "Sprzedających"),
        ("weak_sellers", "Słabi, a sprzedają"), ("median_reviews", "Mediana opinii"),
        ("median_price", "Mediana ceny"), ("indie_share", "Udział indie"),
        ("keyword_hits", "Popularność AC"), ("sponsored_count", "Reklam")]


def write_csv(path: Path, niches: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([c for c, _ in COLS])
        for n in niches:
            w.writerow([n.get(c) for c, _ in COLS])


def write_keywords_csv(path: Path, keywords: list[tuple]):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["keyword", "seed", "hits", "best_pos"])
        w.writerows(keywords)


def _md(text: str) -> str:
    try:
        import markdown
        return markdown.markdown(text, extensions=["tables", "fenced_code"])
    except ImportError:
        return f"<pre style='white-space:pre-wrap'>{html.escape(text)}</pre>"


def write_html(path: Path, market: str, niches: list[dict], keywords: list[tuple],
               advice: str | None = None):
    head = "".join(f"<th data-k='{c}'>{l}</th>" for c, l in COLS)
    rows = []
    for i, n in enumerate(niches):
        cls = {"dobra nisza": "good", "do sprawdzenia": "mid"}.get(n.get("verdict"), "bad")
        cells = "".join(f"<td>{html.escape(str(n.get(c) if n.get(c) is not None else '–'))}</td>" for c, _ in COLS)
        rows.append(f"<tr class='{cls}' onclick='toggle({i})'>{cells}</tr>"
                    f"<tr id='d{i}' class='det' hidden><td colspan='{len(COLS)}'>{_products(n)}</td></tr>")
    kw_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(s or '')}</td><td>{h}</td><td>{p}</td></tr>"
                      for k, s, h, p in keywords[:500])
    doc = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KDP nisze – {market.upper()} – {time.strftime('%Y-%m-%d')}</title>
<style>
body{{font:14px/1.45 system-ui,sans-serif;margin:24px;color:#1d1d1f;background:#fafaf8}}
h1{{font-size:22px}} h2{{font-size:17px;margin-top:32px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;background:#fff}}
th,td{{padding:6px 8px;border-bottom:1px solid #e6e6e1;text-align:left;white-space:nowrap}}
th{{position:sticky;top:0;background:#f0f0eb;cursor:pointer}}
tr.good td:nth-child(2){{color:#0a7a3b;font-weight:600}} tr.mid td:nth-child(2){{color:#a86500;font-weight:600}}
tr.bad td:nth-child(2){{color:#888}} tr:not(.det):hover{{background:#f6f6f2;cursor:pointer}}
.det td{{white-space:normal;background:#fbfbf9}} .det table td{{white-space:normal}}
.note{{color:#666;font-size:12px;max-width:900px}} .advice{{background:#fff;padding:12px 20px;border:1px solid #e6e6e1}}
</style></head><body>
<h1>Analiza nisz KDP (low-content) – {market.upper()}</h1>
<p class="note">Wygenerowano {time.strftime('%Y-%m-%d %H:%M')}. Sprzedaż to zgrubny szacunek z BSR – używaj do
porównań między niszami, nie jako prognozy. „Słabi, a sprzedają” = książki z &lt;50 opiniami i ≥0,5 szt./dzień.
Kliknij wiersz, żeby zobaczyć książki z topu; kliknij nagłówek, żeby sortować.</p>
<div class="wrap"><table id="t"><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{f'<h2>Wnioski agenta</h2><div class="advice">{_md(advice)}</div>' if advice else ''}
<h2>Wszystkie frazy z autocomplete ({len(keywords)})</h2>
<div class="wrap"><table><thead><tr><th>Fraza</th><th>Seed</th><th>Trafienia</th><th>Najl. pozycja</th></tr></thead>
<tbody>{kw_rows}</tbody></table></div>
<script>
function toggle(i){{const r=document.getElementById('d'+i);r.hidden=!r.hidden}}
document.querySelectorAll('#t th').forEach((th,ci)=>{{let asc=false;th.onclick=()=>{{
 asc=!asc;const tb=document.querySelector('#t tbody');const pairs=[];
 const rs=[...tb.children];for(let i=0;i<rs.length;i+=2)pairs.push([rs[i],rs[i+1]]);
 const v=r=>{{const t=r.children[ci].textContent;const n=parseFloat(t.replace(/,/g,''));return isNaN(n)?t:n}};
 pairs.sort((a,b)=>{{const x=v(a[0]),y=v(b[0]);return (x>y?1:x<y?-1:0)*(asc?1:-1)}});
 pairs.forEach(p=>{{tb.appendChild(p[0]);tb.appendChild(p[1])}})}}}});
</script></body></html>"""
    path.write_text(doc, encoding="utf-8")


def _products(n: dict) -> str:
    ps = n.get("top_products") or []
    if not ps:
        return "brak danych"
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(p.get("asin") or ""), html.escape((p.get("title") or "")[:110]),
            p.get("price") or "–", p.get("reviews") if p.get("reviews") is not None else "–",
            p.get("bsr") or "–", p.get("est_sales_day") or 0, "tak" if p.get("indie") else "")
        for p in ps)
    return ("<table><tr><th>ASIN</th><th>Tytuł</th><th>Cena</th><th>Opinie</th><th>BSR</th>"
            f"<th>Sprz./dzień</th><th>Indie</th></tr>{rows}</table>")


def write_json(path: Path, niches):
    path.write_text(json.dumps(niches, ensure_ascii=False, indent=1), encoding="utf-8")
