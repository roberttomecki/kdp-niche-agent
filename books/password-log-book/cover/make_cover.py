#!/usr/bin/env python3
"""Okładka KDP (paperback, pełna: tył + grzbiet + przód) dla Large Print Password Log Book.

Użycie:
  python make_cover.py --all                 # oba formaty, 102 strony
  python make_cover.py --trim 6x9 --pages 102

Wymiary wg KDP: szerokość = 0.125 + format + grzbiet + format + 0.125,
wysokość = format + 0.25. Grzbiet = strony × 0.002252" (biały papier).
Przed wysyłką porównaj z szablonem z KDP Cover Calculator.

Projekt: wieczna zieleń jak płótno starego notesu adresowego, tytuł krojem
Atkinson Hyperlegible Next (zaprojektowanym dla osób słabowidzących), a przy
krawędzi przodu kolumna zakładek A–Z – ta sama, co we wnętrzu. Zakładka „P”
jest wysunięta i mosiężna: jedyny akcent okładki.
Wymaga: pip install playwright (Chromium) – PDF drukuje przeglądarka.
"""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLEED = 0.125
PAPER = 0.002252
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["#"]

C = {
    "ground": "#1F4A40",   # zieleń okładki
    "tab_a": "#2B5E52",    # zakładki, odcień 1
    "tab_b": "#25554A",    # zakładki, odcień 2
    "tab_ink": "#CFE0D8",  # litery na zakładkach
    "brass": "#E3B341",    # wysunięta zakładka P
    "brass_ink": "#1A2E28",
    "text": "#FBFBF8",     # tytuł i tekst
    "muted": "#BFD3CA",
}

FORMATS = {
    "8.5x11": dict(w=8.5, h=11.0, accounts=270, title=1.25, sub=0.30, body=0.165, tab_w=0.48, tab_font=0.15),
    "6x9": dict(w=6.0, h=9.0, accounts=180, title=0.90, sub=0.23, body=0.135, tab_w=0.38, tab_font=0.12),
}


def html(trim: str, pages: int) -> tuple[str, float, float]:
    f = FORMATS[trim]
    spine = pages * PAPER
    W = BLEED + f["w"] + spine + f["w"] + BLEED
    H = f["h"] + 2 * BLEED
    back_x = BLEED
    front_x = BLEED + f["w"] + spine
    safe = 0.5  # odsunięcie treści od linii cięcia (KDP wymaga ≥ 0.125")

    # zakładki: od górnego do dolnego marginesu, wchodzą w spad po prawej
    top, bottom = BLEED + 0.55, BLEED + f["h"] - 0.55
    th = (bottom - top) / len(LETTERS)
    tabs = []
    for i, L in enumerate(LETTERS):
        pulled = L == "P"
        w = f["tab_w"] * (1.9 if pulled else 1.0)
        left = W - BLEED - w
        bg = C["brass"] if pulled else (C["tab_a"] if i % 2 == 0 else C["tab_b"])
        ink = C["brass_ink"] if pulled else C["tab_ink"]
        fs = f["tab_font"] * (1.35 if pulled else 1.0)
        # litera wyśrodkowana w widocznej (po przycięciu) części zakładki
        span_style = "" if pulled else f"width:{f['tab_w']:.3f}in;text-align:center"
        tabs.append(
            f'<div class="tab" style="left:{left:.4f}in;top:{top + i * th + 0.012:.4f}in;'
            f'width:{w + BLEED + 0.05:.4f}in;height:{th - 0.024:.4f}in;background:{bg};color:{ink};'
            f'font-size:{fs:.3f}in;padding-left:{(f["tab_w"] * 0.5 if pulled else 0):.3f}in;'
            f'justify-content:{"flex-start" if pulled else "center"}">'
            f'<span style="{span_style}">{L}</span></div>')
    # zakładka P po wysunięciu nachodzi na przód – przesuwamy tekst, by go nie dotykała
    text_right = W - BLEED - f["tab_w"] * 1.9 - 0.35

    font_url = (HERE / "fonts").as_uri()
    body = f["body"]
    back = f"""
      <div class="back" style="left:{back_x + safe:.3f}in;top:{BLEED + safe + 0.2:.3f}in;width:{f['w'] - 2 * safe:.3f}in">
        <p class="lead">Every login in one place you can actually read.</p>
        <ul>
          <li>Big, clear print and wide lines to write on</li>
          <li>A&#8211;Z tabs printed on the page edge, so the book opens straight to the right letter</li>
          <li>Room for {f['accounts']} websites, with two spare lines for new passwords</li>
          <li>Pages for email accounts and home <span style="white-space:nowrap">Wi-Fi</span></li>
        </ul>
        <p class="spec">{f['w']:g} &times; {f['h']:g} in &nbsp;&nbsp; {pages} pages</p>
      </div>"""
    front = f"""
      <div class="front" style="left:{front_x + safe:.3f}in;top:{BLEED + safe + 0.15:.3f}in;
           width:{text_right - front_x - safe:.3f}in;height:{f['h'] - 2 * safe - 0.3:.3f}in">
        <h1>Password<br>Log Book</h1>
        <p class="sub">Large print with A&#8211;Z tabs</p>
        <div class="card">
          <div class="card-letter">P</div>
          <div class="row"><b>Website:</b><i></i></div>
          <div class="row"><b>Login / Email:</b><i></i></div>
          <div class="row"><b>Password:</b><i></i></div>
          <div class="row light"><b>New password:</b><i></i></div>
        </div>
        <p class="foot">For the websites you use, your logins and passwords</p>
      </div>"""
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: AHN; font-weight: 400; src: url('{font_url}/atkinson-hyperlegible-next-latin-400-normal.woff2'); }}
@font-face {{ font-family: AHN; font-weight: 700; src: url('{font_url}/atkinson-hyperlegible-next-latin-700-normal.woff2'); }}
@font-face {{ font-family: AHN; font-weight: 800; src: url('{font_url}/atkinson-hyperlegible-next-latin-800-normal.woff2'); }}
@page {{ size: {W:.4f}in {H:.4f}in; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
.sheet {{ position: relative; width: {W:.4f}in; height: {H:.4f}in; overflow: hidden;
          background: {C['ground']}; font-family: AHN, sans-serif; color: {C['text']}; }}
.tab {{ position: absolute; display: flex; align-items: center; font-weight: 700;
        border-radius: 0.07in 0 0 0.07in; box-sizing: border-box; }}
.front {{ position: absolute; display: flex; flex-direction: column; }}
h1 {{ margin: 0; font-weight: 800; font-size: {f['title']:.3f}in; line-height: 0.98; letter-spacing: -0.01em; }}
.sub {{ margin: {f['sub'] * 0.9:.3f}in 0 0; font-size: {f['sub']:.3f}in; font-weight: 400; color: {C['muted']}; }}
.foot {{ margin-top: auto; margin-bottom: 0; font-size: {body * 1.2:.3f}in; line-height: 1.35;
         max-width: 80%; color: {C['muted']}; }}
.card {{ margin-top: {f['sub'] * 1.6:.3f}in; background: {C['text']}; color: {C['ground']};
         border-radius: 0.06in; padding: {body * 1.6:.3f}in {body * 1.9:.3f}in {body * 2.0:.3f}in;
         font-size: {body * 1.45:.3f}in; }}
.card-letter {{ text-align: right; font-weight: 800; font-size: {body * 3.2:.3f}in; line-height: 1; }}
.row {{ display: flex; align-items: flex-end; gap: {body:.3f}in; margin-top: {body * 1.5:.3f}in; }}
.row b {{ width: 42%; font-weight: 700; }}
.row i {{ flex: 1; border-bottom: 1.5px solid #8FA79D; height: 0.6em; }}
.row.light b {{ color: #5E7F74; }}
.back {{ position: absolute; font-size: {body * 1.3:.3f}in; line-height: 1.45; }}
.lead {{ font-size: {body * 2.0:.3f}in; font-weight: 700; line-height: 1.2; margin: 0 0 {body * 1.4:.3f}in; }}
ul {{ margin: 0; padding-left: 1.1em; }}
li {{ margin-bottom: {body * 0.6:.3f}in; }}
.spec {{ margin-top: {body * 1.6:.3f}in; color: {C['muted']}; }}
</style></head><body><div class="sheet">{back}{front}{''.join(tabs)}</div></body></html>"""
    return doc, W, H


def render(trim, pages, out: Path):
    from playwright.sync_api import sync_playwright
    doc, W, H = html(trim, pages)
    out.mkdir(parents=True, exist_ok=True)
    src = out / f"cover_{trim}.html"
    src.write_text(doc, encoding="utf-8")
    pdf = out / f"password-log-book_{trim}_cover.pdf"
    png = out / f"password-log-book_{trim}_cover_preview.png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": int(W * 96), "height": int(H * 96)})
        pg.goto(src.as_uri())
        pg.wait_for_timeout(300)
        pg.pdf(path=str(pdf), width=f"{W:.4f}in", height=f"{H:.4f}in", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        pg.screenshot(path=str(png))
        b.close()
    src.unlink()
    return pdf, W, H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trim", choices=FORMATS, default="8.5x11")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--pages", type=int, default=102)
    ap.add_argument("--out", default=str(HERE.parent / "output"))
    a = ap.parse_args()
    for t in (FORMATS if a.all else [a.trim]):
        pdf, W, H = render(t, a.pages, Path(a.out))
        print(f"{pdf}  ({W:.3f} x {H:.3f} in, grzbiet {a.pages * PAPER:.3f} in)")


if __name__ == "__main__":
    main()
