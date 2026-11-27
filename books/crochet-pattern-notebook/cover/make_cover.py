#!/usr/bin/env python3
"""Okładka „Crochet Pattern Notebook” (KDP paperback 8,5 × 11", ze spadem) – seria Golden Stitch.

Użycie:
  python cover/make_cover.py --pages 106 [--seed 1]

Grafika: algorytm Golden Stitch (series/golden-stitch/golden_stitch.js, p5.js) – spirala Vogla
z oczek łańcuszka, kolory przypisane arytmetycznie (n mod 21 + rundy Fibonacciego).
Układ wg złotego podziału: dolny pas tytułu = 11"/φ² ≈ 4,2", środek spirali w złotym punkcie.
Okładka KDP: szerokość = 0,125 + 8,5 + grzbiet + 8,5 + 0,125; wysokość 11,25"; grzbiet = strony × 0,002252".
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
SERIES = BOOK.parent.parent / "series" / "golden-stitch"
sys.path.insert(0, str(SERIES))
from render import render_many  # noqa: E402

for name, file in [("Serif", "Fraunces-SemiBold"), ("Serif-Black", "Fraunces-ExtraBold"),
                   ("Serif-It", "Fraunces-Italic"), ("Sans", "Jost-Regular"),
                   ("Sans-Med", "Jost-Medium"), ("Sans-Bold", "Jost-Bold")]:
    pdfmetrics.registerFont(TTFont(name, str(SERIES / "fonts" / f"{file}.ttf")))

PHI = (1 + 5 ** 0.5) / 2
IN = 72.0
DPI = 300
TRIM_W, TRIM_H, BLEED = 8.5, 11.0, 0.125

GROUND = "#2a1730"      # śliwka
CREAM = "#f6ead6"
AMBER = "#f2a03d"
CORAL = "#e2574c"
TEAL = "#3fa39a"
YARNS = [AMBER, CORAL, "#f6e7cf", TEAL]
INK = HexColor(GROUND)

BAND = TRIM_H / PHI ** 2           # 4,2" – mniejsza część złotego podziału


def art_jobs(seed, out_dir, front_w, panel_h):
    """Konfiguracje Golden Stitch: przód (pełny panel) i tył (echo spirali)."""
    s = DPI
    front = {
        "seed": seed, "W": round(front_w * s), "H": round(panel_h * s),
        # złoty punkt: x = 8,5/φ od lewej krawędzi przodu, y = pas + (11 − pas)/φ² od dołu… liczone od góry obrazu
        "cx": (TRIM_W / PHI) * s, "cy": (panel_h - (BLEED + BAND + (TRIM_H - BAND) / PHI)) * s,
        "count": 1300, "spacing": 0.132 * s, "armsF": 21, "roundsF": True, "jitter": 0.18,
        "tail": True, "tailAngle": 2.75, "unitPx": s, "grain": 1.0,
        "ground": GROUND, "shade": "#12070f", "yarns": YARNS,
    }
    back = dict(front, seed=seed + 1000, W=round((BLEED + TRIM_W) * s),
                cx=(BLEED + 1.05) * s, cy=(BLEED + 1.2) * s,
                count=560, spacing=0.092 * s, armsF=13, tail=False, grain=1.0)
    return [(front, out_dir / f"front_s{seed}.png"), (back, out_dir / f"back_s{seed}.png")]


def to_jpeg(png: Path) -> Path:
    jpg = png.with_suffix(".jpg")
    Image.open(png).convert("RGB").save(jpg, quality=95, subsampling=0, dpi=(DPI, DPI))
    return jpg


def phi_mark(c, x, y, r, col):
    """Znak serii: okrąg przecięty pionową kreską (φ) z oczkiem łańcuszka."""
    c.setStrokeColor(col)
    c.setLineWidth(r * 0.22)
    c.ellipse(x - r * 0.78, y - r * 0.62, x + r * 0.78, y + r * 0.62, stroke=1, fill=0)
    c.line(x, y - r * 1.15, x, y + r * 1.15)


def chain_line(c, x0, x1, y, link, col, lw):
    c.setStrokeColor(col)
    c.setLineWidth(lw)
    n = max(1, int((x1 - x0) / link))
    step = (x1 - x0) / n
    for i in range(n):
        cx = x0 + step * (i + 0.5)
        c.ellipse(cx - step * 0.52, y - link * 0.24, cx + step * 0.52, y + link * 0.24, stroke=1, fill=0)


def fit(text, font, max_w, start):
    size = start
    while pdfmetrics.stringWidth(text, font, size) > max_w and size > 6:
        size -= 0.5
    return size


def spaced(c, x, y, text, font, size, tracking, align="left"):
    w = sum(pdfmetrics.stringWidth(ch, font, size) for ch in text) + tracking * (len(text) - 1)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    c.setFont(font, size)
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + tracking
    return w


def wrap(text, font, size, width):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def front_text(c, fx, band_top):
    """fx = lewa krawędź przyciętego przodu (pt)."""
    x0 = fx + 0.6 * IN
    x1 = fx + TRIM_W * IN - 0.6 * IN
    cream = HexColor(CREAM)
    # łańcuszek na granicy grafiki i pasa
    chain_line(c, fx - BLEED * IN, fx + (TRIM_W + BLEED) * IN, band_top, 0.22 * IN, HexColor(AMBER), 2.2)
    # znak serii
    y = band_top - 0.62 * IN
    phi_mark(c, x0 + 7, y + 4, 8.5, INK)
    c.setFillColor(INK)
    spaced(c, x0 + 22, y, "GOLDEN STITCH NOTEBOOKS", "Sans-Bold", 9.5, 2.2)
    c.setFillColor(HexColor(CORAL))
    spaced(c, x1, y, "40 PROJECTS", "Sans-Bold", 9.5, 2.2, align="right")
    # tytuł
    c.setFillColor(INK)
    size = fit("Crochet", "Serif-Black", x1 - x0, 132)
    yt = y - 0.32 * IN - size * 0.72
    c.setFont("Serif-Black", size)
    c.drawString(x0 - size * 0.04, yt, "Crochet")
    size2 = fit("Pattern Notebook", "Serif", x1 - x0, 60)
    yt2 = yt - size2 * 1.12
    c.setFont("Serif", size2)
    c.drawString(x0, yt2, "Pattern Notebook")
    # podtytuł
    c.setFillColor(HexColor("#6b4a6e"))
    yt3 = yt2 - 0.5 * IN
    spaced(c, x0, yt3, "PROJECT LOG  ·  ROW COUNTER  ·  GAUGE & YARN TRACKER  ·  CHART PAPER",
           "Sans-Med", 9.6, 1.1)


BACK_HEAD = "Every stitch counted. Every project remembered."
BACK_TEXT = ("You finished the blanket. Six months later someone asks for one in blue, and you cannot "
             "remember the hook, the yarn or what you changed in round 14. This notebook keeps all of it, "
             "so every pattern you love can be made again.")
BULLETS = [
    "40 two-page project spreads: project card on the left, row and round tracker on the right",
    "Yarn with dye lot, hook, gauge, finished size, stitches, notions and a swatch box",
    "Tick-off row counter 1–60 and 24 lines of instructions per project",
    "US and UK abbreviations, hook size and yarn weight charts",
    "Hook collection, yarn stash, project index, patterns to try and a gift log",
    "10 pages of chart paper for tapestry, mosaic, C2C and filet designs",
]


def back_text(c, bx, band_top):
    """bx = lewa krawędź przyciętego tyłu (pt)."""
    x0 = bx + 0.6 * IN
    x1 = bx + TRIM_W * IN - 0.6 * IN
    cream = HexColor(CREAM)
    chain_line(c, bx - BLEED * IN, bx + TRIM_W * IN, band_top, 0.22 * IN, HexColor(AMBER), 2.2)
    # nagłówek i opis na tle śliwki
    c.setFillColor(cream)
    y = band_top + 2.55 * IN
    for ln in ("Every stitch counted.", "Every project remembered."):
        c.setFont("Serif", 27)
        c.drawString(x0, y, ln)
        y -= 32
    y -= 6
    c.setFillColor(HexColor("#e9dccb"))
    for ln in wrap(BACK_TEXT, "Sans", 12.5, x1 - x0):
        c.setFont("Sans", 12.5)
        c.drawString(x0, y, ln)
        y -= 17.5
    # lista w kremowym pasie
    c.setFillColor(INK)
    y = band_top - 0.5 * IN
    spaced(c, x0, y, "INSIDE", "Sans-Bold", 9.5, 2.2)
    y -= 22
    for item in BULLETS:
        lines = wrap(item, "Sans", 11.2, x1 - x0 - 16)
        c.setFillColor(HexColor(AMBER))
        c.circle(x0 + 3.5, y + 3.6, 3.1, stroke=0, fill=1)
        c.setFillColor(INK)
        for ln in lines:
            c.setFont("Sans", 11.2)
            c.drawString(x0 + 14, y, ln)
            y -= 14.5
        y -= 4.5
    # stopka: wydawca (lewy dół); prawy dół wolny na kod kreskowy KDP (2 × 1,2")
    c.setFillColor(INK)
    yb = BLEED * IN + 0.45 * IN
    phi_mark(c, x0 + 7, yb + 4, 8.5, INK)
    spaced(c, x0 + 22, yb, "GOLDEN STITCH NOTEBOOKS", "Sans-Bold", 8.5, 2.0)
    c.setFont("Sans", 8.5)
    c.setFillColor(HexColor("#6b4a6e"))
    c.drawString(x0 + 22, yb - 13, "8.5 × 11 in  ·  106 pages  ·  crochet journal & project planner")


def build(pages: int, seed: int, out: Path, art_dir: Path, preview: Path, skip_render=False):
    spine = pages * 0.002252
    full_w = BLEED + TRIM_W + spine + TRIM_W + BLEED
    full_h = TRIM_H + 2 * BLEED
    front_x = BLEED + TRIM_W + spine            # lewa krawędź przodu (bez spadu) w calach
    jobs = art_jobs(seed, art_dir, TRIM_W + BLEED, full_h)
    if not skip_render:
        render_many(jobs)
    front_jpg, back_jpg = (to_jpeg(p) for _, p in jobs)

    c = canvas.Canvas(str(out), pagesize=(full_w * IN, full_h * IN), initialFontName="Sans")
    c.setTitle("Crochet Pattern Notebook – cover")
    c.setAuthor("Golden Stitch Notebooks")
    # tło
    c.setFillColor(HexColor(GROUND))
    c.rect(0, 0, full_w * IN, full_h * IN, stroke=0, fill=1)
    c.drawImage(str(back_jpg), 0, 0, (BLEED + TRIM_W) * IN, full_h * IN)
    c.drawImage(str(front_jpg), front_x * IN, 0, (TRIM_W + BLEED) * IN, full_h * IN)
    # kremowy pas przez całą okładkę (tył, grzbiet, przód)
    band_top = (BLEED + BAND) * IN
    c.setFillColor(HexColor(CREAM))
    c.rect(0, 0, full_w * IN, band_top, stroke=0, fill=1)
    # grzbiet: pasy kolorów przędzy pod łańcuszkiem (bez tekstu – grzbiet < 0,25")
    sx = (BLEED + TRIM_W) * IN
    front_text(c, front_x * IN, band_top)
    back_text(c, BLEED * IN, band_top)
    c.showPage()
    c.save()

    # podgląd PNG + miniatura jak w wynikach Amazona
    import subprocess
    subprocess.run(["pdftoppm", "-r", "60", "-png", "-singlefile", str(out), str(preview.with_suffix(""))], check=True)
    im = Image.open(preview)
    fx0 = round(front_x * 60)
    front = im.crop((fx0, round(BLEED * 60), fx0 + round(TRIM_W * 60), round((BLEED + TRIM_H) * 60)))
    thumb = front.resize((160, round(160 * TRIM_H / TRIM_W)), Image.LANCZOS)
    thumb.save(preview.with_name(preview.stem.replace("_preview", "_thumb160") + ".png"))
    front.save(preview.with_name(preview.stem.replace("_preview", "_front") + ".png"))
    print(f"{out}\n  okładka {full_w:.4f} × {full_h:.2f} in, grzbiet {spine:.4f} in")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=106)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--skip-render", action="store_true", help="użyj już wyrenderowanych PNG")
    a = ap.parse_args()
    out_dir = BOOK / "output"
    art = out_dir / "art"
    art.mkdir(parents=True, exist_ok=True)
    build(a.pages, a.seed, out_dir / "crochet-pattern-notebook_8.5x11_cover.pdf", art,
          out_dir / "crochet-pattern-notebook_8.5x11_cover_preview.png", a.skip_render)


if __name__ == "__main__":
    main()
