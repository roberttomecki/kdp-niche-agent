#!/usr/bin/env python3
"""Okładka KDP (tył + grzbiet + przód) dla „Mileage Log Book for Taxes”, 6 × 9".

Użycie:  python make_cover.py --pages 116
Wymiary: szerokość = 0.125 + 6 + grzbiet + 6 + 0.125, wysokość = 9 + 0.25;
grzbiet = strony × 0.002252" (biały papier). Porównaj z KDP Cover Calculator.

Projekt: atramentowy granat drogowskazu, bursztyn znaków drogowych, a jako
jedyny mocny element – mechaniczny licznik przebiegu z ostatnią cyfrą w trakcie
obrotu. Krój: Atkinson Hyperlegible Next (OFL), wspólny z pierwszą książką.
Wymaga: pip install playwright (Chromium).
"""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "password-log-book" / "cover" / "fonts"
BLEED, PAPER, TW, TH = 0.125, 0.002252, 6.0, 9.0

C = {"ground": "#22324A", "ink": "#16202F", "text": "#F7F7F4", "muted": "#B9C4D3",
     "amber": "#F2B33D", "wheel": "#F7F7F4", "wheel_ink": "#1B2638", "line": "#3A4E6B"}


def html(pages: int):
    spine = pages * PAPER
    W, H = BLEED + TW + spine + TW + BLEED, TH + 2 * BLEED
    fx = BLEED + TW + spine           # lewa krawędź przodu
    safe = 0.5
    font = FONTS.as_uri()
    digits = "184362"
    wheels = "".join(
        f'<div class="w{" roll" if i == len(digits) - 1 else ""}">'
        + (f'<span class="up">{d}</span><span class="dn">{int(d) + 1}</span>' if i == len(digits) - 1 else d)
        + '</div>' for i, d in enumerate(digits))
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: AHN; font-weight: 400; src: url('{font}/atkinson-hyperlegible-next-latin-400-normal.woff2'); }}
@font-face {{ font-family: AHN; font-weight: 700; src: url('{font}/atkinson-hyperlegible-next-latin-700-normal.woff2'); }}
@font-face {{ font-family: AHN; font-weight: 800; src: url('{font}/atkinson-hyperlegible-next-latin-800-normal.woff2'); }}
@page {{ size: {W:.4f}in {H:.4f}in; margin: 0; }}
html, body {{ margin: 0; }}
.sheet {{ position: relative; width: {W:.4f}in; height: {H:.4f}in; overflow: hidden;
          background: {C['ground']}; font-family: AHN, sans-serif; color: {C['text']}; }}
/* przerywana linia środkowa drogi wzdłuż dolnej krawędzi przodu i tyłu */
.road {{ position: absolute; left: {fx:.3f}in; right: 0; bottom: {BLEED + 0.32:.3f}in; height: 0.06in;
         background: repeating-linear-gradient(90deg, {C['amber']} 0 0.42in, transparent 0.42in 0.74in); opacity: .9; }}
.front {{ position: absolute; left: {fx + safe:.3f}in; top: {BLEED + safe + 0.2:.3f}in;
          width: {TW - 2 * safe:.3f}in; height: {TH - 2 * safe - 0.75:.3f}in; display: flex; flex-direction: column; }}
h1 {{ margin: 0; font-weight: 800; font-size: 0.86in; line-height: .95; letter-spacing: -0.01em; }}
.sub {{ margin: 0.2in 0 0; font-size: 0.24in; color: {C['muted']}; line-height: 1.25; }}
.odo {{ margin-top: 0.9in; display: flex; align-items: center; gap: 0.06in; }}
.w {{ width: 0.66in; height: 0.92in; border-radius: 0.06in; background: {C['wheel']}; color: {C['wheel_ink']};
      font-weight: 800; font-size: 0.64in; display: flex; align-items: center; justify-content: center;
      box-shadow: inset 0 0.1in 0.12in rgba(0,0,0,.18), inset 0 -0.1in 0.12in rgba(0,0,0,.18); }}
.w.roll {{ background: {C['amber']}; position: relative; overflow: hidden; flex-direction: column; justify-content: flex-start; }}
.w.roll span {{ display: block; height: 0.92in; line-height: 0.92in; text-align: center; }}
.w.roll .up {{ margin-top: -0.12in; }}
.unit {{ margin-left: 0.12in; font-size: 0.26in; font-weight: 700; color: {C['muted']}; }}
.foot {{ margin-top: auto; font-size: 0.17in; line-height: 1.4; color: {C['muted']}; }}
.back {{ position: absolute; left: {BLEED + safe:.3f}in; top: {BLEED + safe + 0.2:.3f}in;
         width: {TW - 2 * safe:.3f}in; font-size: 0.165in; line-height: 1.5; }}
.lead {{ font-size: 0.28in; font-weight: 700; line-height: 1.2; margin: 0 0 0.25in; }}
ul {{ margin: 0; padding-left: 1.1em; }} li {{ margin-bottom: 0.1in; }}
.spec {{ margin-top: 0.25in; color: {C['muted']}; }}
.note {{ margin-top: 0.3in; font-size: 0.13in; color: {C['muted']}; }}
</style></head><body><div class="sheet">
  <div class="road"></div>
  <div class="back">
    <p class="lead">Every trip on one line, ready for tax time.</p>
    <ul>
      <li>Room for 2,000 trips: date, destination and purpose, odometer start and end, miles</li>
      <li>Mark each trip as business or personal</li>
      <li>Page totals, an annual summary and pages for parking, tolls and vehicle costs</li>
      <li>Vehicle details for up to two cars</li>
      <li>Fits in a glove box</li>
    </ul>
    <p class="spec">6 &times; 9 in &nbsp;&nbsp; {pages} pages</p>
    <p class="note">This logbook is a place to record your driving, not tax advice.</p>
  </div>
  <div class="front">
    <h1>Mileage<br>Log Book</h1>
    <p class="sub">For taxes, business<br>and personal driving</p>
    <div class="odo">{wheels}<span class="unit">mi</span></div>
    <p class="foot">Room for 2,000 trips, your expenses<br>and a yearly summary</p>
  </div>
</div></body></html>"""
    return doc, W, H


def render(pages: int, out: Path):
    from playwright.sync_api import sync_playwright
    doc, W, H = html(pages)
    out.mkdir(parents=True, exist_ok=True)
    src = out / "_cover.html"
    src.write_text(doc, encoding="utf-8")
    pdf = out / "mileage-log-book_6x9_cover.pdf"
    png = out / "mileage-log-book_6x9_cover_preview.png"
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
    ap.add_argument("--pages", type=int, default=116)
    ap.add_argument("--out", default=str(HERE / "output"))
    a = ap.parse_args()
    pdf, W, H = render(a.pages, Path(a.out))
    print(f"{pdf}  ({W:.3f} x {H:.3f} in, grzbiet {a.pages * PAPER:.3f} in)")


if __name__ == "__main__":
    main()
