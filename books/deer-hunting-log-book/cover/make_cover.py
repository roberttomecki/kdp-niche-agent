#!/usr/bin/env python3
"""Okładka KDP (tył + grzbiet + przód) dla „Deer Hunting Log Book”, 6 × 9".

Użycie:  python cover/make_cover.py --pages 110
Wymiary: szerokość = 0.125 + 6 + grzbiet + 6 + 0.125, wysokość = 9 + 0.25;
grzbiet = strony × 0.002252" (biały papier). Porównaj z KDP Cover Calculator.

Projekt „Contour Vigil” (cover/PHILOSOPHY.md): mapa poziomic na całej okładce,
łańcuch tropów jelenia przecinający poziomice i jeden pomarańczowy punkt –
stanowisko myśliwego. Krój tytułu: National Park (OFL, inspirowany tablicami
parków narodowych USA), opisy: Jura i DM Mono (OFL). Grafika wektorowa (reportlab).
Wymaga: pip install reportlab numpy matplotlib
"""
import argparse
import math
from pathlib import Path

import numpy as np
from matplotlib import contour as mcontour, pyplot as plt
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
for name, file in [("Park", "NationalPark-Bold.ttf"), ("ParkReg", "NationalPark-Regular.ttf"),
                   ("Jura", "Jura-Medium.ttf"), ("JuraL", "Jura-Light.ttf"), ("Mono", "DMMono-Regular.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))

BLEED, PAPER, TW, TH = 0.125, 0.002252, 6.0, 9.0
IN = 72.0
GROUND = HexColor("#1C2820")
CONTOUR = HexColor("#3E5040")
INDEX = HexColor("#506550")
BONE = HexColor("#ECE4D2")
BLAZE = HexColor("#F2641C")


def alpha(col, a):
    return Color(col.red, col.green, col.blue, alpha=a)


# --- teren ---------------------------------------------------------------------
def terrain(X, Y, fx):
    """Wysokość terenu (cale → umowne metry). Wzgórze ze stanowiskiem leży na przodzie."""
    hills = [  # (x, y, wysokość, promień)
        (fx + 4.15, 2.55, 1.00, 1.15),   # wzgórze ze stanowiskiem
        (fx + 1.10, 1.30, 0.45, 0.85),
        (fx + 5.40, 6.20, 0.70, 1.30),
        (fx + 2.20, 7.40, 0.35, 1.60),
        (2.10, 6.60, 0.95, 1.35),        # tył
        (4.60, 2.20, 0.60, 1.10),
        (1.00, 1.60, 0.40, 0.90),
        (fx - 0.40, 4.40, 0.45, 1.50),   # przez grzbiet
    ]
    Z = np.zeros_like(X)
    for x, y, h, r in hills:
        Z += h * np.exp(-(((X - x) ** 2 + (Y - y) ** 2) / (2 * r * r)))
    Z += 0.10 * np.sin(X * 0.9 + Y * 0.45) + 0.07 * np.cos(Y * 1.3 - X * 0.35)  # łagodne fałdy
    Z += 0.035 * np.sin(X * 3.1 + 1.7) * np.cos(Y * 2.6 - 0.4)                    # drobna rzeźba
    return Z


def contours(W, H, fx, levels):
    xs, ys = np.linspace(0, W, 760), np.linspace(0, H, 563)
    X, Y = np.meshgrid(xs, ys)
    Z = terrain(X, Y, fx)
    fig = plt.figure()
    cs = plt.contour(X, Y, Z, levels=levels)
    segs = [cs.allsegs[i] for i in range(len(levels))]
    plt.close(fig)
    return segs


# --- tropy ---------------------------------------------------------------------
def bezier(p0, p1, p2, p3, n=600):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def hoof(c, x, y, ang, s, col):
    """Trop jelenia: dwie wydłużone racice zwrócone ostrzem w kierunku marszu."""
    c.saveState()
    c.translate(x * IN, y * IN)
    c.rotate(math.degrees(ang) - 90)
    c.setFillColor(col)
    L, Wd = 1.0 * s * IN, 0.34 * s * IN
    for side in (-1, 1):
        p = c.beginPath()
        g = side * 0.05 * Wd                                     # wąska szczelina między racicami
        p.moveTo(g, L * 0.50)                                    # czubek przy osi tropu
        p.curveTo(g + side * Wd * 0.55, L * 0.42, g + side * Wd * 1.05, L * 0.05, g + side * Wd * 0.95, -L * 0.28)
        p.curveTo(g + side * Wd * 0.88, -L * 0.50, g + side * Wd * 0.35, -L * 0.56, g + side * Wd * 0.12, -L * 0.40)
        p.curveTo(g + side * Wd * 0.02, -L * 0.25, g, L * 0.20, g, L * 0.50)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def track_line(c, pts, step, s, a0, a1, stop):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    total = d[-1] - stop
    k, pos = 0, 0.15
    while pos < total:
        i = int(np.searchsorted(d, pos))
        x, y = pts[i]
        dx, dy = pts[min(i + 3, len(pts) - 1)] - pts[max(i - 3, 0)]
        ang = math.atan2(dy, dx)
        side = 1 if k % 2 else -1
        nx, ny = -math.sin(ang) * side * 0.055, math.cos(ang) * side * 0.055
        a = a0 + (a1 - a0) * (pos / total) ** 1.4
        hoof(c, x + nx, y + ny, ang, s, alpha(BONE, a))
        pos += step
        k += 1


# --- rysowanie -----------------------------------------------------------------
def fit(text, font, width_in):
    return width_in * IN / pdfmetrics.stringWidth(text, font, 1)


def build(out: Path, pages: int) -> Path:
    spine = pages * PAPER
    W, H = BLEED + TW + spine + TW + BLEED, TH + 2 * BLEED
    fx = BLEED + TW + spine                     # lewa krawędź przodu (linia grzbietu)
    path = out / "deer-hunting-log-book_6x9_cover.pdf"
    c = canvas.Canvas(str(path), pagesize=(W * IN, H * IN), initialFontName="Mono")
    c.setTitle("Deer Hunting Log Book – cover")
    c.setAuthor("Robert Tomecki")

    c.setFillColor(GROUND)
    c.rect(0, 0, W * IN, H * IN, stroke=0, fill=1)

    # poziomice
    levels = np.linspace(-0.18, 1.26, 49)
    segs = contours(W, H, fx, levels)
    c.setLineJoin(1)
    c.setLineCap(1)
    for i, lev_segs in enumerate(segs):
        idx = i % 5 == 0
        c.setStrokeColor(INDEX if idx else CONTOUR)
        c.setLineWidth(0.85 if idx else 0.42)
        for s in lev_segs:
            if len(s) < 3:
                continue
            p = c.beginPath()
            p.moveTo(*(s[0] * IN))
            for x, y in s[1:]:
                p.lineTo(x * IN, y * IN)
            c.drawPath(p, stroke=1, fill=0)

    # wysokości na kilku poziomicach głównych (z „wycięciem” w linii)
    def elev_label(target, level_i, text):
        best = None
        for s in segs[level_i]:
            dd = np.hypot(s[:, 0] - target[0], s[:, 1] - target[1])
            j = int(np.argmin(dd))
            if best is None or dd[j] < best[0]:
                best = (dd[j], s, j)
        _, s, j = best
        x, y = s[j]
        dx, dy = s[min(j + 2, len(s) - 1)] - s[max(j - 2, 0)]
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        c.saveState()
        c.translate(x * IN, y * IN)
        c.rotate(ang)
        tw = pdfmetrics.stringWidth(text, "Mono", 5.2)
        c.setFillColor(GROUND)
        c.rect(-tw / 2 - 2.5, -3.2, tw + 5, 6.4, stroke=0, fill=1)
        c.setFillColor(alpha(BONE, 0.55))
        c.setFont("Mono", 5.2)
        c.drawCentredString(0, -1.8, text)
        c.restoreState()

    elev_label((fx + 5.05, 1.35), 25, "1240")
    elev_label((fx + 3.00, 4.35), 15, "1190")
    elev_label((4.20, 1.15), 20, "1215")

    # ramka mapy na przodzie z podziałką
    m = 0.42
    L, R, B, T = fx + m, W - BLEED - m, BLEED + m, H - BLEED - m
    c.setStrokeColor(alpha(BONE, 0.55))
    c.setLineWidth(0.5)
    c.rect(L * IN, B * IN, (R - L) * IN, (T - B) * IN, stroke=1, fill=0)
    c.setFont("Mono", 5.2)
    c.setFillColor(alpha(BONE, 0.5))
    step = 0.25
    n = 0
    x = L + step
    while x < R - 0.01:
        h = 0.07 if n % 4 == 3 else 0.035
        c.line(x * IN, B * IN, x * IN, (B + h) * IN)
        c.line(x * IN, T * IN, x * IN, (T - h) * IN)
        if n % 4 == 3:
            c.drawCentredString(x * IN, (B - 0.12) * IN, f"91°{14 - n // 4:02d}'W")
        x += step
        n += 1
    n = 0
    y = B + step
    while y < T - 0.01:
        h = 0.07 if n % 4 == 3 else 0.035
        c.line(L * IN, y * IN, (L + h) * IN, y * IN)
        c.line(R * IN, y * IN, (R - h) * IN, y * IN)
        y += step
        n += 1

    # tropy: łańcuch przez poziomice ku stanowisku
    stand = np.array([fx + 3.62, 2.86])
    pts = bezier(np.array([fx + 0.78, 0.92]), np.array([fx + 1.65, 1.15]),
                 np.array([fx + 1.70, 2.70]), stand)
    track_line(c, pts, step=0.22, s=0.115, a0=0.18, a1=0.95, stop=0.44)

    # stanowisko – jedyny pomarańczowy element
    sx, sy = stand * IN
    c.setStrokeColor(BLAZE)
    c.setLineWidth(0.6)
    c.circle(sx, sy, 0.17 * IN, stroke=1, fill=0)
    c.setFillColor(BLAZE)
    r = 0.075 * IN
    p = c.beginPath()
    p.moveTo(sx, sy + r)
    p.lineTo(sx - r * 0.95, sy - r * 0.62)
    p.lineTo(sx + r * 0.95, sy - r * 0.62)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setFont("Mono", 6.4)
    c.setFillColor(BONE)
    c.drawString(sx + 0.27 * IN, sy + 2, "STAND 3")
    c.setFillColor(alpha(BONE, 0.7))
    c.drawString(sx + 0.27 * IN, sy - 7.5, "06:48  WIND NW 4")

    # tytuł
    tx = L + 0.32
    tw = (R - L) - 0.64
    size = fit("DEER HUNTING", "Park", tw)
    c.setFillColor(BONE)
    c.setFont("Park", size)
    top = T - 0.42
    c.drawString(tx * IN, (top * IN) - size * 0.74, "DEER HUNTING")
    size2 = fit("LOG BOOK", "Park", tw)
    size2 = min(size2, size * 1.32)
    c.setFont("Park", size2)
    y2 = (top * IN) - size * 0.74 - size2 * 0.86
    c.drawString(tx * IN, y2, "LOG BOOK")
    # cienka linia i podtytuł
    ly = y2 - 0.24 * IN
    c.setStrokeColor(BLAZE)
    c.setLineWidth(1.4)
    c.line(tx * IN, ly, (tx + 0.55) * IN, ly)
    c.setFillColor(BONE)
    c.setFont("Jura", 13.5)
    c.drawString(tx * IN, ly - 0.3 * IN, "Record every hunt: weather, wind,")
    c.drawString(tx * IN, ly - 0.3 * IN - 17, "deer sightings, stands and harvests")
    c.setFont("Mono", 6.6)
    c.setFillColor(alpha(BONE, 0.7))
    c.drawString(tx * IN, ly - 0.3 * IN - 40, "80 HUNTS  /  8 HARVEST RECORDS  /  TRAIL CAMS  /  MAPS")

    # tył
    bl = BLEED + 0.6
    by = H - BLEED - 0.95
    bw = TW - 1.2
    c.setFillColor(BONE)
    c.setFont("Park", 26)
    c.drawString(bl * IN, by * IN, "EVERY SIT, ON RECORD.")
    c.setStrokeColor(BLAZE)
    c.setLineWidth(1.2)
    c.line(bl * IN, (by - 0.22) * IN, (bl + 0.45) * IN, (by - 0.22) * IN)
    blurb = ("The deer you saw, the wind you sat in, the stand that finally paid off. "
             "Write it down while it is fresh, and next season the pattern is yours.")
    c.setFont("Jura", 11.5)
    y = by - 0.55
    for ln in wrap(blurb, "Jura", 11.5, bw):
        c.drawString(bl * IN, y * IN, ln)
        y -= 0.24
    y -= 0.18
    items = ["80 hunt pages with wind compass, weather and moon phase",
             "Deer-seen tables for bucks, does and fawns",
             "8 harvest records with antler measurements and a photo space",
             "Stand & blind locations, trail-camera log, property maps",
             "Season summaries to compare year after year"]
    c.setFont("Jura", 10.5)
    for it in items:
        c.setFillColor(BLAZE)
        c.rect(bl * IN, (y + 0.045) * IN, 4, 4, stroke=0, fill=1)
        c.setFillColor(BONE)
        for k, ln in enumerate(wrap(it, "Jura", 10.5, bw - 0.2)):
            c.drawString((bl + 0.18) * IN, y * IN, ln)
            y -= 0.2
        y -= 0.06
    c.setFont("Mono", 6.6)
    c.setFillColor(alpha(BONE, 0.65))
    c.drawString(bl * IN, (BLEED + 0.62) * IN, "6 × 9 IN  /  110 PAGES")

    c.showPage()
    c.save()
    return path


def wrap(text, font, size, width_in):
    words, out, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width_in * IN:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", type=int, default=110)
    ap.add_argument("--out", default=str(HERE.parent / "output"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    p = build(out, a.pages)
    spine = a.pages * PAPER
    print(f"{p}  ({2 * BLEED + 2 * TW + spine:.3f} × {TH + 2 * BLEED:.2f} in, grzbiet {spine:.3f} in)")


if __name__ == "__main__":
    main()
