#!/usr/bin/env python3
"""Wnętrze „Deer Hunting Log Book” (KDP paperback, 6 × 9", bez spadu).

Użycie:
  python make_interior.py --author "Imię Nazwisko"

Specyfikacja KDP (bez bleed): strona PDF = dokładnie format (6 × 9"),
margines wewnętrzny 0.5" (wymagane ≥0.375" do 150 stron), zewnętrzny,
górny i dolny ≥0.45" (wymagane ≥0.25"). Fonty osadzone (DejaVu Sans).
"""
import argparse
import math
from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "password-log-book" / "fonts"
pdfmetrics.registerFont(TTFont("Sans", str(FONTS / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Sans-Bold", str(FONTS / "DejaVuSans-Bold.ttf")))

INCH = 72.0
W, H = 6.0 * INCH, 9.0 * INCH
GUTTER, OUTER, TOP, BOTTOM = 0.5 * INCH, 0.45 * INCH, 0.5 * INCH, 0.5 * INCH
INK = Color(0.11, 0.12, 0.10)
GRID = Color(0.60, 0.61, 0.58)
HEAD_FILL = Color(0.87, 0.87, 0.84)
SOFT = Color(0.36, 0.37, 0.34)

HUNT_PAGES = 80
HARVEST_PAGES = 8
CAMERA_PAGES = 4
MAP_PAGES = 4
NOTES_PAGES = 4

class Book:
    def __init__(self, path: Path, author: str, title: str):
        self.c = canvas.Canvas(str(path), pagesize=(W, H), initialFontName="Sans")
        self.c.setTitle(title)
        self.c.setAuthor(author)
        self.c.setCreator("kdp-niche-agent / deer-hunting-log-book")
        self.page, self.author, self.title = 1, author, title

    def box(self):
        """Obszar treści (x0, y0, x1, y1) z marginesami; strony nieparzyste są po prawej."""
        if self.page % 2:   # prawa strona: grzbiet po lewej
            return GUTTER, BOTTOM, W - OUTER, H - TOP
        return OUTER, BOTTOM, W - GUTTER, H - TOP

    def next(self):
        self.c.showPage()
        self.page += 1

    # --- elementy -------------------------------------------------------------
    def heading(self, text, size=16):
        x0, _, x1, y1 = self.box()
        c = self.c
        c.setFillColor(INK)
        c.setFont("Sans-Bold", size)
        c.drawString(x0, y1 - size, text)
        return y1 - size * 2.5

    def table(self, cols, rows, top, bottom, footer=None, first_col_values=None):
        """Tabela z nagłówkiem; zwraca y dolnej krawędzi."""
        x0, _, x1, _ = self.box()
        c, width = self.c, x1 - x0
        head_h = 0.42 * INCH
        footer_h = 0.32 * INCH if footer else 0
        row_h = (top - bottom - head_h - footer_h) / rows
        xs = [x0]
        for _, share in cols:
            xs.append(xs[-1] + share * width)
        xs[-1] = x1
        # nagłówek
        c.setFillColor(HEAD_FILL)
        c.rect(x0, top - head_h, width, head_h, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Sans-Bold", 8.5)
        for (lines, _), a, b in zip(cols, xs, xs[1:]):
            mid = (a + b) / 2
            if len(lines) == 1:
                c.drawCentredString(mid, top - head_h / 2 - 3, lines[0])
            else:
                c.drawCentredString(mid, top - head_h / 2 + 2.5, lines[0])
                c.drawCentredString(mid, top - head_h / 2 - 8.5, lines[1])
        # wiersze
        c.setStrokeColor(GRID)
        c.setLineWidth(0.6)
        y = top - head_h
        for r in range(rows):
            y -= row_h
            c.line(x0, y, x1, y)
            if first_col_values:
                c.setFont("Sans", 9)
                c.setFillColor(INK)
                c.drawString(x0 + 4, y + row_h / 2 - 3, first_col_values[r])
        table_bottom = y
        for xx in xs:  # pionowe linie
            c.line(xx, table_bottom, xx, top)
        c.line(x0, top, x1, top)
        if footer:
            c.setFont("Sans-Bold", 8.5)
            c.setFillColor(INK)
            fy = table_bottom - footer_h + 9
            c.drawString(x0, fy, footer)
        return table_bottom

    def lines(self, top, bottom, step=0.34 * INCH, label_rows=None):
        x0, _, x1, _ = self.box()
        c = self.c
        c.setStrokeColor(GRID)
        c.setLineWidth(0.6)
        y, i = top, 0
        while y - step > bottom:
            y -= step
            if label_rows and i < len(label_rows) and label_rows[i]:
                c.setFont("Sans-Bold", 9.5)
                c.setFillColor(INK)
                c.drawString(x0, y + 4, label_rows[i])
                lw = pdfmetrics.stringWidth(label_rows[i], "Sans-Bold", 9.5) + 8
                c.line(x0 + lw, y, x1, y)
            else:
                c.line(x0, y, x1, y)
            i += 1

    def paragraphs(self, top, items, size=10.5, bullet=False):
        x0, _, x1, _ = self.box()
        c, y = self.c, top
        c.setFillColor(INK)
        c.setFont("Sans", size)
        indent = 12 if bullet else 0
        for p in items:
            first = True
            for line in wrap(p, "Sans", size, x1 - x0 - indent):
                if bullet and first:
                    c.drawString(x0, y, "•")
                c.drawString(x0 + indent, y, line)
                y -= size * 1.45
                first = False
            y -= size * 0.55
        return y

    def save(self):
        self.c.save()


def wrap(text, font, size, width):
    words, out, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out




# --- drobne elementy formularza ------------------------------------------------
def field(c, x, y, label, x_end, size=9, bold=True):
    """Etykieta i linia do wpisania aż do x_end."""
    c.setFillColor(INK)
    c.setFont("Sans-Bold" if bold else "Sans", size)
    c.drawString(x, y, label)
    lw = pdfmetrics.stringWidth(label, "Sans-Bold" if bold else "Sans", size) + 5
    c.setStrokeColor(GRID)
    c.setLineWidth(0.6)
    c.line(x + lw, y - 2, x_end, y - 2)


def options(c, x, y, label, choices, size=8.5, gap=9):
    """„Etykieta: ○ A ○ B …” – zwraca x końca."""
    c.setFillColor(INK)
    c.setFont("Sans-Bold", size)
    c.drawString(x, y, label)
    x += pdfmetrics.stringWidth(label, "Sans-Bold", size) + 6
    c.setFont("Sans", size)
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    for ch in choices:
        c.circle(x + 3.2, y + 3, 3.2, stroke=1, fill=0)
        x += 9.5
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, "Sans", size) + gap
    return x


def checkbox(c, x, y, s=7.5):
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.rect(x, y - 1, s, s, stroke=1, fill=0)


def compass(c, cx, cy, r):
    """Róża wiatrów do zakreślenia kierunku wiatru."""
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    c.circle(cx, cy, r * 0.55, stroke=1, fill=0)
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    for i, n in enumerate(names):
        a = math.radians(90 - i * 45)
        c.setStrokeColor(INK if i % 2 == 0 else GRID)
        c.line(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55,
               cx + math.cos(a) * r * 0.88, cy + math.sin(a) * r * 0.88)
        c.setFillColor(INK)
        c.setFont("Sans-Bold" if i % 2 == 0 else "Sans", 7 if i % 2 == 0 else 5.8)
        tx, ty = cx + math.cos(a) * (r + 7), cy + math.sin(a) * (r + 7) - 2.3
        c.drawCentredString(tx, ty, n)
    c.setFillColor(INK)
    c.circle(cx, cy, 1.4, stroke=0, fill=1)


def moon(c, cx, cy, r, phase):
    """phase 0..7: nów, sierp, I kwadra, garb, pełnia, garb, III kwadra, sierp (cień = czerń)."""
    p = c.beginPath()
    p.circle(cx, cy, r)
    c.saveState()
    c.clipPath(p, stroke=0, fill=0)
    lit = phase / 4 if phase <= 4 else (8 - phase) / 4        # 0 nów … 1 pełnia
    c.setFillColor(INK)
    c.rect(cx - r, cy - r, 2 * r, 2 * r, stroke=0, fill=1)   # całość w cieniu
    c.setFillColor(white)
    right = phase <= 4                                        # przybywa → oświetlona prawa strona
    if lit > 0:
        # połowa oświetlona + elipsa terminatora
        if right:
            c.rect(cx, cy - r, r, 2 * r, stroke=0, fill=1)
        else:
            c.rect(cx - r, cy - r, r, 2 * r, stroke=0, fill=1)
        k = abs(1 - 2 * lit) * r                              # półoś pozioma terminatora
        if lit > 0.5:
            c.setFillColor(white)
        else:
            c.setFillColor(INK)
        if k > 0.1:
            c.ellipse(cx - k, cy - r, cx + k, cy + r, stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.circle(cx, cy, r, stroke=1, fill=0)


def section(c, x0, x1, y, text, size=9.5):
    c.setFillColor(INK)
    c.setFont("Sans-Bold", size)
    c.drawString(x0, y, text.upper())
    w = pdfmetrics.stringWidth(text.upper(), "Sans-Bold", size)
    c.setStrokeColor(INK)
    c.setLineWidth(0.9)
    c.line(x0 + w + 6, y + 3, x1, y + 3)


def dot_grid(c, x0, y0, x1, y1, step=0.25 * INCH):
    c.setFillColor(GRID)
    y = y0 + step / 2
    while y < y1:
        x = x0 + step / 2
        while x < x1:
            c.circle(x, y, 0.55, stroke=0, fill=1)
            x += step
        y += step


# --- strony ---------------------------------------------------------------------
HOW_TO = [
    "Fill in one Hunt page every time you go out – even on days you see nothing. Blank days are data too.",
    "Circle the wind direction on the compass and note the temperature, sky and moon phase.",
    "Log every deer you see: the time, how many bucks, does and fawns, where they came from and what they did.",
    "If you take a shot, note the distance and result, then fill in a Harvest record at the back.",
    "Keep your stands, trail-camera checks and property sketches in their own sections.",
    "At the end of the season, total it up on the Season summary page – your patterns will start to show.",
]
SAFETY = ("Always know and follow your state's hunting regulations, tagging rules and firearm "
          "and tree-stand safety practices.")
GEAR = ["Hunting license & tags", "Weapon", "Ammo / arrows", "Knife & sharpener", "Rangefinder",
        "Binoculars", "Headlamp + batteries", "Safety harness", "Blaze orange", "Scent control spray",
        "Calls / rattle bag", "Decoy", "Field-dressing gloves", "Drag rope", "Game bags",
        "First-aid kit", "Water & snacks", "Hand warmers", "Rain gear", "Phone & power bank",
        "Trail-camera SD cards", "Pull-up rope", "Marking tape", "Seat cushion"]


def hunt_page(b):
    c = b.c
    x0, y0, x1, y1 = b.box()
    mid = (x0 + x1) / 2
    y = y1 - 12
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 13)
    c.drawString(x0, y, "HUNT #")
    c.setStrokeColor(GRID); c.setLineWidth(0.6)
    c.line(x0 + 52, y - 2, x0 + 100, y - 2)
    field(c, mid - 10, y, "Date:", x1)
    y -= 22
    field(c, x0, y, "Location / stand:", x1)
    y -= 20
    field(c, x0, y, "Time in:", x0 + 118)
    field(c, x0 + 128, y, "Time out:", x0 + 250)
    field(c, x0 + 260, y, "Hours:", x1)
    y -= 20
    options(c, x0, y, "Weapon:", ["Bow", "Crossbow", "Muzzleloader", "Rifle", "Shotgun"], gap=6.5)
    # pogoda
    y -= 14
    box_h = 1.62 * INCH
    c.setStrokeColor(INK); c.setLineWidth(0.8)
    c.roundRect(x0, y - box_h, x1 - x0, box_h, 5, stroke=1, fill=0)
    r = 0.47 * INCH
    ccx, ccy = x0 + r + 16, y - box_h / 2 - 4
    compass(c, ccx, ccy, r)
    c.setFont("Sans-Bold", 7.5); c.setFillColor(INK)
    c.drawCentredString(ccx, y - 11, "WIND – circle")
    wx = x0 + 2 * r + 38
    wy = y - 16
    field(c, wx, wy, "Temp:", wx + 78, size=8.5)
    c.setFont("Sans", 8.5); c.drawString(wx + 80, wy, "°F")
    field(c, wx + 100, wy, "Wind speed:", x1 - 30, size=8.5)
    c.setFont("Sans", 8.5); c.drawString(x1 - 27, wy, "mph")
    wy -= 19
    options(c, wx, wy, "Sky:", ["Clear", "Cloudy", "Rain", "Snow", "Fog"], size=8, gap=5)
    wy -= 19
    field(c, wx, wy, "Barometer:", wx + 110, size=8.5)
    options(c, wx + 116, wy, "", ["Rising", "Falling"], size=8, gap=5)
    wy -= 24
    c.setFont("Sans-Bold", 8.5); c.setFillColor(INK)
    c.drawString(wx, wy, "Moon:")
    mx = wx + 38
    for ph in range(8):
        moon(c, mx + ph * 18.5, wy + 3, 5.6, ph)
    y -= box_h + 18
    # obserwacje
    section(c, x0, x1, y, "Deer seen")
    cols = [(("Time",), 0.15), (("Bucks",), 0.12), (("Does",), 0.12), (("Fawns",), 0.12),
            (("From / to – what they did",), 0.49)]
    bottom = b.table(cols, 6, y - 7, y - 7 - 0.3 * INCH - 6 * 0.3 * INCH)
    y = bottom - 18
    options(c, x0, y, "Shot taken:", ["Yes", "No"])
    field(c, x0 + 128, y, "Distance:", x0 + 225)
    c.setFont("Sans", 8.5); c.drawString(x0 + 227, y, "yds")
    options(c, x0 + 255, y, "", ["Hit", "Miss"], gap=5)
    y -= 20
    field(c, x0, y, "Calls / scent / decoy used:", x1)
    y -= 20
    section(c, x0, x1, y, "Notes")
    b.lines(y - 2, y0, step=0.3 * INCH)


def harvest_page(b, n):
    c = b.c
    x0, y0, x1, y1 = b.box()
    mid = (x0 + x1) / 2
    y = y1 - 12
    c.setFillColor(INK); c.setFont("Sans-Bold", 13)
    c.drawString(x0, y, f"HARVEST RECORD {n}")
    y -= 24
    rows = [("Date:", "Time:"), ("Location / stand:", None), ("Weapon & load / broadhead:", None),
            ("Shot distance (yds):", "Shot placement:"), ("Tracked (yds):", "Recovered at:"),
            ("Tag / permit #:", "Check-in #:")]
    for a, bb in rows:
        if bb:
            field(c, x0, y, a, mid - 8)
            field(c, mid + 4, y, bb, x1)
        else:
            field(c, x0, y, a, x1)
        y -= 21
    options(c, x0, y, "Deer:", ["Buck", "Doe", "Button buck"])
    y -= 18
    section(c, x0, x1, y, "Antlers & body")
    cols = [(("",), 0.34), (("Left",), 0.22), (("Right",), 0.22), (("Total",), 0.22)]
    labels = ["Points", "Main beam", "Inside spread", "Est. weight (lbs)", "Est. age"]
    bottom = b.table(cols, 5, y - 7, y - 7 - 0.3 * INCH - 5 * 0.29 * INCH, first_col_values=labels)
    y = bottom - 14
    # zdjęcie
    ph = 2.0 * INCH
    c.setStrokeColor(GRID); c.setLineWidth(0.8); c.setDash(3, 3)
    c.rect(x0, y - ph, x1 - x0, ph, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(SOFT); c.setFont("Sans", 9)
    c.drawCentredString((x0 + x1) / 2, y - ph / 2 - 3, "Tape a photo here")
    y -= ph + 16
    section(c, x0, x1, y, "The story")
    b.lines(y - 2, y0, step=0.3 * INCH)


def build(out: Path, author: str) -> tuple[Path, int]:
    title = "Deer Hunting Log Book"
    path = out / "deer-hunting-log-book_6x9_interior.pdf"
    b = Book(path, author, title)
    c = b.c

    # 1 – tytuł
    x0, y0, x1, y1 = b.box()
    mid = (x0 + x1) / 2
    compass(c, mid, y1 - 1.25 * INCH, 0.42 * INCH)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 30)
    c.drawCentredString(mid, y1 - 2.55 * INCH, "DEER HUNTING")
    c.drawCentredString(mid, y1 - 2.55 * INCH - 36, "LOG BOOK")
    c.setFont("Sans", 11.5)
    c.setFillColor(SOFT)
    c.drawCentredString(mid, y1 - 2.55 * INCH - 64, "Hunts · weather · sightings · harvests")
    b.lines(y0 + 2.6 * INCH, y0 + 0.4 * INCH, step=0.42 * INCH,
            label_rows=["This book belongs to:", "Phone:", "Season(s):", "If found, please call:"])
    b.next()
    # 2 – prawa autorskie
    x0, y0, x1, y1 = b.box()
    c.setFont("Sans", 8.5)
    c.setFillColor(SOFT)
    y = y0 + 70
    for ln in [title, f"Copyright © 2026 {author}. All rights reserved.",
               "No part of this book may be copied without permission."] + wrap(SAFETY, "Sans", 8.5, x1 - x0):
        c.drawString(x0, y, ln)
        y -= 12
    b.next()
    # 3 – jak używać
    y = b.heading("How to use this log book")
    y = b.paragraphs(y, HOW_TO, bullet=True)
    x0, y0, x1, _ = b.box()
    c.setFont("Sans", 9); c.setFillColor(SOFT)
    yy = y0 + 40
    for ln in wrap(SAFETY, "Sans", 9, x1 - x0):
        c.drawString(x0, yy, ln)
        yy -= 12
    # klucz faz księżyca
    c.setFont("Sans-Bold", 8.5); c.setFillColor(INK)
    ky = y - 20
    c.drawString(x0, ky, "Moon phases on the Hunt pages:")
    names = ["New", "Wax. cres.", "1st qtr", "Wax. gib.", "Full", "Wan. gib.", "3rd qtr", "Wan. cres."]
    step = (x1 - x0) / 8
    for i, n in enumerate(names):
        cx = x0 + step * (i + 0.5)
        moon(c, cx, ky - 20, 7, i)
        c.setFont("Sans", 6.5); c.setFillColor(INK)
        c.drawCentredString(cx, ky - 38, n)
    b.next()
    # 4 – dane myśliwego i sezony
    y = b.heading("Hunter & license information", size=14)
    x0, y0, x1, _ = b.box()
    for lab in ["Name:", "Address:", "Phone:", "Emergency contact:", "Hunting license #:",
                "Hunter education #:", "Deer tags #:", "State / zone / unit:"]:
        field(c, x0, y, lab, x1)
        y -= 23
    y -= 4
    section(c, x0, x1, y, "Season dates")
    cols = [(("Season",), 0.36), (("Opens",), 0.32), (("Closes",), 0.32)]
    b.table(cols, 6, y - 7, y0 + 0.2 * INCH,
            first_col_values=["Archery", "Crossbow", "Muzzleloader", "Rifle / firearm", "Youth", ""])
    b.next()
    # 5 – lista sprzętu
    y = b.heading("Gear checklist", size=14)
    x0, y0, x1, _ = b.box()
    colw = (x1 - x0) / 2
    rows = len(GEAR) // 2 + 4
    step = (y - y0) / rows
    for i in range(rows * 2):
        col, row = divmod(i, rows)
        xx, yy = x0 + col * colw, y - row * step - 6
        checkbox(c, xx, yy)
        if i - col * rows < len(GEAR) // 2 and (col * (len(GEAR) // 2) + row) < len(GEAR):
            c.setFont("Sans", 9.5); c.setFillColor(INK)
            c.drawString(xx + 13, yy, GEAR[col * (len(GEAR) // 2) + row])
        else:
            c.setStrokeColor(GRID); c.setLineWidth(0.6)
            c.line(xx + 13, yy - 2, xx + colw - 12, yy - 2)
    b.next()
    # 6–7 – stanowiska
    for _ in range(2):
        y = b.heading("Stands & blinds", size=14)
        x0, y0, x1, _ = b.box()
        block = (y - y0) / 3
        for k in range(3):
            yy = y - k * block
            field(c, x0, yy, "Stand name / #:", x1)
            yy -= 19
            options(c, x0, yy, "Type:", ["Tree stand", "Ladder", "Ground blind", "Saddle"], gap=6)
            yy -= 19
            field(c, x0, yy, "GPS:", x1)
            yy -= 19
            field(c, x0, yy, "Best wind(s):", (x0 + x1) / 2 - 6)
            field(c, (x0 + x1) / 2 + 4, yy, "Access:", x1)
            yy -= 19
            field(c, x0, yy, "Notes:", x1)
            yy -= 19
            c.setStrokeColor(GRID)
            while yy > y - (k + 1) * block + 22:
                c.line(x0, yy - 2, x1, yy - 2)
                yy -= 19
        b.next()
    # 8–11 – szkice terenu
    for _ in range(MAP_PAGES):
        x0, y0, x1, y1 = b.box()
        field(c, x0, y1 - 12, "Property / map:", x1 - 0.7 * INCH)
        top = y1 - 26
        c.setStrokeColor(INK); c.setLineWidth(0.8)
        c.rect(x0, y0, x1 - x0, top - y0, stroke=1, fill=0)
        dot_grid(c, x0, y0, x1, top)
        # strzałka północy
        nx, ny = x1 - 0.3 * INCH, y1 - 10
        c.setFillColor(INK)
        p = c.beginPath(); p.moveTo(nx, ny + 9); p.lineTo(nx - 5, ny - 6); p.lineTo(nx, ny - 2); p.close()
        c.drawPath(p, stroke=0, fill=1)
        p = c.beginPath(); p.moveTo(nx, ny + 9); p.lineTo(nx + 5, ny - 6); p.lineTo(nx, ny - 2); p.close()
        c.setStrokeColor(INK); c.drawPath(p, stroke=1, fill=0)
        c.setFont("Sans-Bold", 8); c.drawCentredString(nx - 14, ny - 3, "N")
        b.next()
    # polowania
    for _ in range(HUNT_PAGES):
        hunt_page(b)
        b.next()
    # pozyskania
    for n in range(1, HARVEST_PAGES + 1):
        harvest_page(b, n)
        b.next()
    # fotopułapki
    for _ in range(CAMERA_PAGES):
        y = b.heading("Trail camera log", size=14)
        x0, y0, x1, _ = b.box()
        cols = [(("Date",), 0.14), (("Camera /", "site"), 0.18), (("Time",), 0.13), (("Bucks",), 0.11),
                (("Does",), 0.11), (("Notes",), 0.33)]
        b.table(cols, 18, y + 6, y0)
        b.next()
    # podsumowania sezonów
    for _ in range(2):
        y = b.heading("Season summary", size=14)
        x0, y0, x1, _ = b.box()
        field(c, x0, y, "Season:", x0 + 150)
        y -= 12
        cols = [(("",), 0.55), (("Total",), 0.45)]
        labels = ["Days hunted", "Hours on stand", "Deer seen", "Bucks seen", "Does & fawns seen",
                  "Shots taken", "Deer harvested", "Best stand", "Best wind", "Best time of day"]
        bottom = b.table(cols, len(labels), y, y - 0.3 * INCH - len(labels) * 0.27 * INCH,
                         first_col_values=labels)
        y = bottom - 18
        section(c, x0, x1, y, "Lessons for next season")
        b.lines(y - 2, y0, step=0.3 * INCH)
        b.next()
    # notatki
    for i in range(NOTES_PAGES):
        y = b.heading("Notes", size=14)
        _, y0, _, _ = b.box()
        b.lines(y + 6, y0)
        if i < NOTES_PAGES - 1:
            b.next()
    total = b.page
    if total % 2:
        b.next()
        y = b.heading("Notes", size=14)
        b.lines(y + 6, b.box()[1])
        total += 1
    b.save()
    return path, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--author", required=True)
    ap.add_argument("--out", default=str(HERE / "output"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    p, n = build(out, a.author)
    print(f"{p}  ({n} stron)")


if __name__ == "__main__":
    main()
