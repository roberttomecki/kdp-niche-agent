#!/usr/bin/env python3
"""Wnętrze „Crochet Pattern Notebook” (KDP paperback, 8,5 × 11", bez spadu) – seria Golden Stitch.

Użycie:
  python make_interior.py

106 stron: strona tytułowa, jak korzystać, skróty US/UK, tabele szydełek i grubości włóczki,
moje szydełka, zapas włóczki, spis projektów, 40 projektów na rozkładówkach (karta projektu po lewej,
licznik rzędów po prawej), papier w kratkę do wzorów kolorowych, wzory do zrobienia, prezenty, notatki.

KDP bez spadu: strona = 8,5 × 11", margines od grzbietu 0,625" (wymagane ≥ 0,375" do 150 stron),
pozostałe 0,5" (wymagane ≥ 0,25"). Fonty osadzone (Fraunces + Jost, OFL).
"""
import argparse
import sys
from pathlib import Path

from reportlab.lib.colors import Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
SERIES = HERE.parent.parent / "series" / "golden-stitch"
FONTS = SERIES / "fonts"
for name, file in [("Serif", "Fraunces-SemiBold"), ("Serif-Black", "Fraunces-ExtraBold"),
                   ("Serif-It", "Fraunces-Italic"), ("Sans", "Jost-Regular"),
                   ("Sans-Med", "Jost-Medium"), ("Sans-Bold", "Jost-Bold")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / f"{file}.ttf")))

INCH = 72.0
W, H = 8.5 * INCH, 11 * INCH
GUTTER, OUTER, TOP, BOTTOM = 0.625 * INCH, 0.5 * INCH, 0.5 * INCH, 0.5 * INCH
INK = Color(0.16, 0.10, 0.18)          # ciemna śliwka jak tło okładki
SOFT = Color(0.42, 0.38, 0.44)
LINE = Color(0.62, 0.59, 0.63)
FILL = Color(0.93, 0.91, 0.92)
ACCENT = Color(0.85, 0.55, 0.20)       # bursztyn przędzy (drukuje się jako szarość – to tylko akcent)

PROJECTS = 40
GRAPH_PAGES = 10
TITLE = "Crochet Pattern Notebook"


class Book:
    def __init__(self, path: Path):
        self.c = canvas.Canvas(str(path), pagesize=(W, H), initialFontName="Sans")
        self.c.setTitle(TITLE)
        self.c.setAuthor("Golden Stitch Notebooks")
        self.c.setCreator("kdp-niche-agent / crochet-pattern-notebook")
        self.page = 1

    def box(self):
        if self.page % 2:      # prawa strona: grzbiet po lewej
            return GUTTER, BOTTOM, W - OUTER, H - TOP
        return OUTER, BOTTOM, W - GUTTER, H - TOP

    def next(self):
        self.c.showPage()
        self.page += 1

    def header(self, title, right=None, size=20):
        """Nagłówek z cienką linią i „ściegiem” – zwraca y pod nagłówkiem."""
        x0, _, x1, y1 = self.box()
        c = self.c
        c.setFillColor(INK)
        c.setFont("Serif", size)
        c.drawString(x0, y1 - size * 0.85, title)
        if right:
            c.setFont("Sans", 9)
            c.setFillColor(SOFT)
            c.drawRightString(x1, y1 - size * 0.85, right)
        y = y1 - size * 0.85 - 9
        chain(c, x0, x1, y)
        return y - 16

    def folio(self):
        x0, y0, x1, _ = self.box()
        c = self.c
        c.setFont("Sans", 8)
        c.setFillColor(SOFT)
        if self.page % 2:
            c.drawRightString(x1, y0 + 3, str(self.page))
        else:
            c.drawString(x0, y0 + 3, str(self.page))

    def save(self):
        self.c.save()


# --- drobne elementy --------------------------------------------------------------
def chain(c, x0, x1, y, link=7.0):
    """Linia z oczek łańcuszka (zamiast zwykłej kreski)."""
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    n = int((x1 - x0) / link)
    step = (x1 - x0) / n
    for i in range(n):
        cx = x0 + step * (i + 0.5)
        c.ellipse(cx - step * 0.52, y - 1.7, cx + step * 0.52, y + 1.7, stroke=1, fill=0)


def field(c, x, y, label, x_end, size=9):
    c.setFillColor(INK)
    c.setFont("Sans-Med", size)
    c.drawString(x, y, label)
    lx = x + pdfmetrics.stringWidth(label, "Sans-Med", size) + 5
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(lx, y - 2, x_end, y - 2)


def section(c, x0, x1, y, text):
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 8.5)
    c.drawString(x0, y, text.upper())
    w = pdfmetrics.stringWidth(text.upper(), "Sans-Bold", 8.5)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(x0 + w + 6, y + 3, x1, y + 3)


def checkbox(c, x, y, s=7.0):
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.7)
    c.rect(x, y, s, s, stroke=1, fill=0)


def circle_opt(c, x, y, label, size=8.5):
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.7)
    c.circle(x + 3.5, y + 3, 3.5, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Sans", size)
    c.drawString(x + 10, y, label)
    return x + 10 + pdfmetrics.stringWidth(label, "Sans", size) + 12


def star(c, cx, cy, r):
    import math
    p = c.beginPath()
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        a = math.pi / 2 + k * math.pi / 5
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        (p.moveTo if k == 0 else p.lineTo)(x, y)
    p.close()
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.7)
    c.drawPath(p, stroke=1, fill=0)


def table(c, x0, x1, top, bottom, cols, rows, head_h=20, numbered=None, check_col=False):
    """Tabela: cols = [(nagłówek, udział)], zwraca listę y wierszy."""
    width = x1 - x0
    xs = [x0]
    for _, share in cols:
        xs.append(xs[-1] + share * width)
    xs[-1] = x1
    c.setFillColor(FILL)
    c.rect(x0, top - head_h, width, head_h, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 8)
    for (label, _), a, b in zip(cols, xs, xs[1:]):
        c.drawCentredString((a + b) / 2, top - head_h / 2 - 3, label.upper())
    row_h = (top - head_h - bottom) / rows
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    ys = []
    for r in range(rows + 1):
        y = top - head_h - r * row_h
        c.line(x0, y, x1, y)
        ys.append(y)
    c.line(x0, top, x1, top)
    for x in xs:
        c.line(x, top, x, bottom)
    if numbered:
        c.setFont("Sans", 7.5)
        c.setFillColor(SOFT)
        for r in range(rows):
            c.drawCentredString((xs[0] + xs[1]) / 2, ys[r] - row_h / 2 - 2.5, str(numbered + r))
    if check_col:
        for r in range(rows):
            s = min(8, row_h * 0.5)
            checkbox(c, (xs[-2] + xs[-1]) / 2 - s / 2, ys[r] - row_h / 2 - s / 2, s)
    return ys, xs


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


def ruled(c, x0, x1, top, bottom, step=0.3 * INCH):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    y = top - step
    while y >= bottom - 0.1:
        c.line(x0, y, x1, y)
        y -= step


# --- strony -----------------------------------------------------------------------
def title_page(b, emblem):
    x0, y0, x1, y1 = b.box()
    c = b.c
    mid = (x0 + x1) / 2
    if emblem and emblem.exists():
        s = 3.0 * INCH
        c.drawImage(str(emblem), mid - s / 2, y1 - s - 0.55 * INCH, s, s, mask="auto")
    c.setFillColor(INK)
    c.setFont("Serif-Black", 40)
    c.drawCentredString(mid, y1 - 4.35 * INCH, "Crochet")
    c.setFont("Serif", 30)
    c.drawCentredString(mid, y1 - 4.95 * INCH, "Pattern Notebook")
    c.setFont("Serif-It", 12.5)
    c.setFillColor(SOFT)
    c.drawCentredString(mid, y1 - 5.4 * INCH, "Every stitch counted. Every project remembered.")
    y = y1 - 6.6 * INCH
    for label in ("This notebook belongs to", "Contact", "Started on"):
        field(c, x0 + 0.6 * INCH, y, label, x1 - 0.6 * INCH, size=11)
        y -= 0.62 * INCH
    c.setFont("Sans", 8)
    c.setFillColor(SOFT)
    c.drawCentredString(mid, y0 + 0.15 * INCH, "Golden Stitch Notebooks")


def howto_page(b):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("How to use this notebook")
    items = [
        ("Project index (p. 8–9)", "Give every project a number and a line in the index, so you can find any pattern in seconds."),
        ("40 project spreads (p. 10–89)", "The left page is the project card: pattern source, yarn with dye lot, hook, gauge, "
         "finished size, stitches, notions, a swatch or photo box and your rating. The right page is the row and round "
         "tracker with a tick-off counter for rows 1–60."),
        ("Reference pages (p. 3–7)", "US and UK stitch abbreviations, hook sizes, yarn weights, your hook collection and your yarn stash."),
        ("Graph paper (p. 90–99)", "Chart tapestry, mosaic, C2C and filet crochet designs. Bold lines every 5 squares."),
        ("Patterns to try and gift log (p. 100–103)", "Save ideas for later and remember who received what you made."),
        ("Tip", "Tape the yarn label or a 10 cm snip of yarn into the swatch box. Next time you will know exactly what you used."),
    ]
    for head, text in items:
        c.setFillColor(INK)
        c.setFont("Sans-Bold", 11)
        c.drawString(x0, y, head)
        y -= 15
        c.setFont("Sans", 10.5)
        c.setFillColor(INK)
        for ln in wrap(text, "Sans", 10.5, x1 - x0):
            c.drawString(x0, y, ln)
            y -= 14
        y -= 14
    b.folio()


ABBR = [
    ("ch", "chain", "ch", "chain"),
    ("sl st", "slip stitch", "ss", "slip stitch"),
    ("sc", "single crochet", "dc", "double crochet"),
    ("hdc", "half double crochet", "htr", "half treble"),
    ("dc", "double crochet", "tr", "treble"),
    ("tr", "treble (triple) crochet", "dtr", "double treble"),
    ("dtr", "double treble", "trtr", "triple treble"),
    ("sc2tog", "single crochet 2 together", "dc2tog", "double crochet 2 together"),
    ("inc", "increase (2 sts in 1)", "inc", "increase"),
    ("dec", "decrease", "dec", "decrease"),
    ("MR", "magic ring", "MR", "magic ring"),
    ("BLO / FLO", "back / front loop only", "BLO / FLO", "back / front loop only"),
    ("FPdc / BPdc", "front / back post dc", "FPtr / BPtr", "front / back post treble"),
    ("sk", "skip", "miss", "miss"),
    ("yo", "yarn over", "yoh", "yarn over hook"),
    ("st(s)", "stitch(es)", "st(s)", "stitch(es)"),
    ("sp", "space", "sp", "space"),
    ("rep", "repeat", "rep", "repeat"),
    ("RS / WS", "right / wrong side", "RS / WS", "right / wrong side"),
    ("tch", "turning chain", "tch", "turning chain"),
    ("PM", "place marker", "PM", "place marker"),
    ("tog", "together", "tog", "together"),
]


def abbreviations_page(b):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Crochet abbreviations", right="US terms  ·  UK terms")
    rows = len(ABBR)
    ys, xs = table(c, x0, x1, y, y0 + 0.75 * INCH,
                   [("US", 0.16), ("US meaning", 0.34), ("UK", 0.16), ("UK meaning", 0.34)], rows, head_h=22)
    rh = ys[0] - ys[1]
    for r, row in enumerate(ABBR):
        yy = ys[r] - rh / 2 - 3.2
        for k, val in enumerate(row):
            c.setFont("Sans-Bold" if k in (0, 2) else "Sans", 9.5)
            c.setFillColor(INK)
            c.drawString(xs[k] + 7, yy, val)
    c.setFont("Serif-It", 10)
    c.setFillColor(SOFT)
    c.drawString(x0, y0 + 0.35 * INCH, "Same name, different stitch: a UK “double crochet” is a US single crochet. Check which terms your pattern uses.")
    b.folio()


HOOKS = [("2.25", "B-1"), ("2.75", "C-2"), ("3.25", "D-3"), ("3.5", "E-4"), ("3.75", "F-5"), ("4.0", "G-6"),
         ("4.5", "7"), ("5.0", "H-8"), ("5.5", "I-9"), ("6.0", "J-10"), ("6.5", "K-10½"), ("8.0", "L-11"),
         ("9.0", "M/N-13"), ("10.0", "N/P-15"), ("15.0", "P/Q"), ("16.0", "Q"), ("19.0", "S")]
WEIGHTS = [("0", "Lace", "fingering, 10-count thread", "1.5–2.25 mm"),
           ("1", "Super Fine", "sock, fingering, baby", "2.25–3.5 mm"),
           ("2", "Fine", "sport, baby", "3.5–4.5 mm"),
           ("3", "Light", "DK, light worsted", "4.5–5.5 mm"),
           ("4", "Medium", "worsted, afghan, aran", "5.5–6.5 mm"),
           ("5", "Bulky", "chunky, craft, rug", "6.5–9 mm"),
           ("6", "Super Bulky", "super chunky, roving", "9–15 mm"),
           ("7", "Jumbo", "jumbo, roving", "15 mm and larger")]


def charts_page(b):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Hook sizes & yarn weights")
    section(c, x0, x1, y, "Crochet hook sizes")
    y -= 10
    rows = len(HOOKS)
    half = (rows + 1) // 2
    colw = (x1 - x0 - 0.3 * INCH) / 2
    for side in range(2):
        part = HOOKS[side * half:(side + 1) * half]
        ax = x0 + side * (colw + 0.3 * INCH)
        ys, xs = table(c, ax, ax + colw, y, y - 20 - len(part) * 17,
                       [("Metric (mm)", 0.5), ("US size", 0.5)], len(part), head_h=20)
        for r, (mm, us) in enumerate(part):
            c.setFont("Sans", 9.5)
            c.setFillColor(INK)
            c.drawCentredString((xs[0] + xs[1]) / 2, ys[r] - 12, mm)
            c.drawCentredString((xs[1] + xs[2]) / 2, ys[r] - 12, us)
    y = y - 20 - half * 17 - 0.45 * INCH
    section(c, x0, x1, y, "Yarn weights (standard yarn weight system)")
    y -= 10
    ys, xs = table(c, x0, x1, y, y - 22 - len(WEIGHTS) * 26,
                   [("No.", 0.08), ("Category", 0.2), ("Also called", 0.42), ("Typical hook", 0.3)], len(WEIGHTS), head_h=22)
    for r, row in enumerate(WEIGHTS):
        for k, val in enumerate(row):
            c.setFont("Sans-Bold" if k < 2 else "Sans", 9.5)
            c.setFillColor(INK)
            c.drawString(xs[k] + 7, ys[r] - 16, val)
    c.setFont("Serif-It", 9.5)
    c.setFillColor(SOFT)
    c.drawString(x0, y0 + 0.35 * INCH, "Hook letters vary between brands – always trust the millimetre size printed on the hook.")
    b.folio()


def hooks_page(b):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("My hooks")
    ys, xs = table(c, x0, x1, y, y - 22 - len(HOOKS) * 22,
                   [("Size (mm)", 0.14), ("US", 0.12), ("Have", 0.1), ("Brand / material", 0.4), ("Notes", 0.24)],
                   len(HOOKS), head_h=22)
    for r, (mm, us) in enumerate(HOOKS):
        c.setFont("Sans", 9.5)
        c.setFillColor(INK)
        c.drawCentredString((xs[0] + xs[1]) / 2, ys[r] - 14, mm)
        c.drawCentredString((xs[1] + xs[2]) / 2, ys[r] - 14, us)
        checkbox(c, (xs[2] + xs[3]) / 2 - 3.5, ys[r] - 14.5)
    y = ys[-1] - 0.45 * INCH
    section(c, x0, x1, y, "Wish list & other tools")
    ruled(c, x0, x1, y - 4, y0 + 0.2 * INCH)
    b.folio()


def stash_page(b, part):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Yarn stash", right=f"page {part} of 2")
    table(c, x0, x1, y, y0 + 0.2 * INCH,
          [("Brand & name", 0.25), ("Wt", 0.06), ("Fiber", 0.13), ("Colour / dye lot", 0.2),
           ("Yds / m", 0.1), ("Qty", 0.07), ("Stored / project", 0.19)], 26, head_h=22)
    b.folio()


def index_page(b, start):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Project index", right=f"projects {start}–{start + 19}")
    ys, xs = table(c, x0, x1, y, y0 + 0.2 * INCH,
                   [("No.", 0.07), ("Project", 0.39), ("Pages", 0.12), ("Started", 0.13),
                    ("Finished", 0.13), ("Done", 0.16)], 20, head_h=22, numbered=start, check_col=True)
    rh = ys[0] - ys[1]
    c.setFont("Sans", 8.5)
    c.setFillColor(SOFT)
    for r in range(20):
        n = start + r
        p = 10 + (n - 1) * 2
        c.drawCentredString((xs[2] + xs[3]) / 2, ys[r] - rh / 2 - 3, f"{p}–{p + 1}")
    b.folio()


STITCHES = ["ch", "sl st", "sc", "hdc", "dc", "tr", "MR", "BLO", "FLO", "FPdc", "BPdc",
            "puff", "bobble", "popcorn", "shell", "V-st", "cluster", "C2C"]
NOTIONS = ["stitch markers", "tapestry needle", "safety eyes", "stuffing", "buttons", "zipper", "blocking mats"]


def project_card(b, n):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Project card", right=f"PROJECT No. {n}")
    field(c, x0, y, "Project", x1, size=11)
    y -= 26
    half = (x0 + x1) / 2
    field(c, x0, y, "Pattern / designer", x1)
    y -= 22
    field(c, x0, y, "Source (book, link, page)", x1)
    y -= 22
    field(c, x0, y, "Made for", half - 12)
    field(c, half, y, "Occasion", x1)
    y -= 22
    field(c, x0, y, "Started", half - 12)
    field(c, half, y, "Finished", x1)
    y -= 22
    c.setFont("Sans-Med", 9)
    c.setFillColor(INK)
    c.drawString(x0, y, "Level")
    xx = x0 + 34
    for lv in ("Beginner", "Easy", "Intermediate", "Experienced"):
        xx = circle_opt(c, xx, y, lv)
    y -= 30

    section(c, x0, x1, y, "Yarn")
    y -= 8
    ys, _ = table(c, x0, x1, y, y - 18 - 3 * 21,
                  [("Brand & name", 0.3), ("Wt (0–7)", 0.11), ("Fiber", 0.15), ("Colour / dye lot", 0.22),
                   ("Yds/m", 0.11), ("Skeins", 0.11)], 3, head_h=18)
    y = ys[-1] - 26

    section(c, x0, x1, y, "Hook & gauge")
    y -= 22
    field(c, x0, y, "Hook (mm / US)", half - 12)
    field(c, half, y, "Finished size", x1)
    gy_top = y - 14
    sq = 1.45 * INCH
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.7)
    c.setDash(2, 2)
    c.rect(x0, gy_top - sq, sq, sq, stroke=1, fill=0)
    c.setDash()
    c.setFont("Sans", 7.5)
    c.setFillColor(SOFT)
    c.drawCentredString(x0 + sq / 2, gy_top - sq / 2 + 4, "tape your")
    c.drawCentredString(x0 + sq / 2, gy_top - sq / 2 - 7, "gauge swatch here")
    fx = x0 + sq + 0.3 * INCH
    fy = gy_top - 12
    for lab in ("Pattern gauge (sts × rows / 4 in)", "My gauge (sts × rows / 4 in)", "Blocking", "Yarn used (total)"):
        field(c, fx, fy, lab, x1)
        fy -= 25
    y = gy_top - sq - 26

    section(c, x0, x1, y, "Stitches used")
    y -= 18
    cols = 6
    cw = (x1 - x0) / cols
    for i, s in enumerate(STITCHES):
        cx = x0 + (i % cols) * cw
        cy = y - (i // cols) * 16
        checkbox(c, cx, cy - 1)
        c.setFont("Sans", 9)
        c.setFillColor(INK)
        c.drawString(cx + 11, cy, s)
    y -= (len(STITCHES) + cols - 1) // cols * 16 + 12
    section(c, x0, x1, y, "Notions")
    y -= 18
    cols = 4
    cw = (x1 - x0) / cols
    for i, s in enumerate(NOTIONS + ["_______________"]):
        cx = x0 + (i % cols) * cw
        cy = y - (i // cols) * 16
        checkbox(c, cx, cy - 1)
        c.setFont("Sans", 9)
        c.setFillColor(INK)
        c.drawString(cx + 11, cy, s)
    y -= 2 * 16 + 12

    # zdjęcie / próbka + notatki
    bottom = y0 + 0.62 * INCH
    pw = 2.9 * INCH
    c.setStrokeColor(SOFT)
    c.setLineWidth(0.7)
    c.rect(x0, bottom, pw, y - bottom, stroke=1, fill=0)
    c.setFont("Sans", 8)
    c.setFillColor(SOFT)
    c.drawCentredString(x0 + pw / 2, (y + bottom) / 2 + 4, "photo, yarn label")
    c.drawCentredString(x0 + pw / 2, (y + bottom) / 2 - 7, "or yarn snip")
    nx0 = x0 + pw + 0.25 * INCH
    c.setFont("Sans-Bold", 8.5)
    c.setFillColor(INK)
    c.drawString(nx0, y - 9, "NOTES & CHANGES")
    ruled(c, nx0, x1, y - 12, bottom, step=0.27 * INCH)
    # ocena
    c.setFont("Sans-Med", 9)
    c.setFillColor(INK)
    c.drawString(x0, y0 + 0.3 * INCH, "Rating")
    for k in range(5):
        star(c, x0 + 48 + k * 17, y0 + 0.3 * INCH + 3.5, 6)
    xx = x0 + 3.0 * INCH
    c.drawString(xx, y0 + 0.3 * INCH, "Make again?")
    xx = circle_opt(c, xx + 62, y0 + 0.3 * INCH, "Yes")
    circle_opt(c, xx, y0 + 0.3 * INCH, "No")
    b.folio()


def tracker_page(b, n):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Rows & rounds", right=f"PROJECT No. {n}")
    c.setFont("Sans-Bold", 8.5)
    c.setFillColor(INK)
    c.drawString(x0, y, "ROW COUNTER – TICK AS YOU GO")
    y -= 8
    per = 30
    cw = (x1 - x0) / per
    for row in range(2):
        for k in range(per):
            num = row * per + k + 1
            bx = x0 + k * cw
            by = y - (row + 1) * 18
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.rect(bx + 0.8, by, cw - 1.6, 15, stroke=1, fill=0)
            c.setFont("Sans", 6.2)
            c.setFillColor(SOFT)
            c.drawCentredString(bx + cw / 2, by + 9.5, str(num))
    y -= 2 * 18 + 22
    field(c, x0, y, "Starting chain / magic ring", (x0 + x1) / 2 - 10)
    field(c, (x0 + x1) / 2, y, "Repeat", x1)
    y -= 18
    table(c, x0, x1, y, y0 + 1.25 * INCH,
          [("Row / Rnd", 0.11), ("Instructions", 0.66), ("Sts", 0.1), ("Done", 0.13)], 24, head_h=20,
          check_col=True)
    c.setFont("Sans-Bold", 8.5)
    c.setFillColor(INK)
    c.drawString(x0, y0 + 1.25 * INCH - 16, "FINISHING, SEAMS & EDGING")
    ruled(c, x0, x1, y0 + 1.25 * INCH - 18, y0 + 0.2 * INCH, step=0.27 * INCH)
    b.folio()


def graph_page(b, k):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Chart paper", right="tapestry · mosaic · C2C · filet")
    field(c, x0, y, "Design", (x0 + x1) / 2 - 10)
    field(c, (x0 + x1) / 2, y, "Project No.", x1)
    y -= 14
    s = 0.2 * INCH
    cols = int((x1 - x0) / s)
    rows = int((y - y0 - 0.2 * INCH) / s)
    gx0 = x0 + ((x1 - x0) - cols * s) / 2
    gy1 = y
    for i in range(cols + 1):
        heavy = i % 5 == 0
        c.setStrokeColor(SOFT if heavy else LINE)
        c.setLineWidth(0.8 if heavy else 0.35)
        c.line(gx0 + i * s, gy1, gx0 + i * s, gy1 - rows * s)
    for j in range(rows + 1):
        heavy = j % 5 == 0
        c.setStrokeColor(SOFT if heavy else LINE)
        c.setLineWidth(0.8 if heavy else 0.35)
        c.line(gx0, gy1 - j * s, gx0 + cols * s, gy1 - j * s)
    b.folio()


def wishlist_page(b, part):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Patterns to try", right=f"page {part} of 2")
    table(c, x0, x1, y, y0 + 0.2 * INCH,
          [("Pattern", 0.32), ("Designer / source", 0.3), ("Yarn & hook", 0.24), ("Made", 0.14)], 24,
          head_h=22, check_col=True)
    b.folio()


def gift_page(b, part):
    x0, y0, x1, y1 = b.box()
    c = b.c
    y = b.header("Gift log", right=f"page {part} of 2")
    table(c, x0, x1, y, y0 + 0.2 * INCH,
          [("Date", 0.12), ("For", 0.2), ("Occasion", 0.17), ("What I made", 0.3), ("Care notes", 0.21)], 24,
          head_h=22)
    b.folio()


def notes_page(b):
    x0, y0, x1, y1 = b.box()
    y = b.header("Notes")
    ruled(b.c, x0, x1, y + 4, y0 + 0.2 * INCH)
    b.folio()


def build(out: Path, emblem: Path | None) -> tuple[Path, int]:
    b = Book(out)
    title_page(b, emblem); b.next()                         # 1
    howto_page(b); b.next()                                 # 2
    abbreviations_page(b); b.next()                         # 3
    charts_page(b); b.next()                                # 4
    hooks_page(b); b.next()                                 # 5
    stash_page(b, 1); b.next(); stash_page(b, 2); b.next()  # 6–7
    index_page(b, 1); b.next(); index_page(b, 21); b.next() # 8–9
    for n in range(1, PROJECTS + 1):                        # 10–89
        assert b.page % 2 == 0, "karta projektu musi być po lewej"
        project_card(b, n); b.next()
        tracker_page(b, n); b.next()
    for k in range(GRAPH_PAGES):                            # 90–99
        graph_page(b, k); b.next()
    wishlist_page(b, 1); b.next(); wishlist_page(b, 2); b.next()   # 100–101
    gift_page(b, 1); b.next(); gift_page(b, 2); b.next()           # 102–103
    for i in range(3):                                      # 104–106
        notes_page(b)
        if i < 2:
            b.next()
    pages = b.page
    b.save()
    return out, pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "output" / "crochet-pattern-notebook_8.5x11_interior.pdf"))
    ap.add_argument("--emblem", default=str(HERE / "output" / "art" / "emblem_gray.png"))
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out, pages = build(Path(a.out), Path(a.emblem))
    print(f"{out}  ({pages} stron)")
    if pages % 2:
        sys.exit("Liczba stron nieparzysta!")


if __name__ == "__main__":
    main()
