#!/usr/bin/env python3
"""Wnętrze „Mileage Log Book for Taxes” (KDP paperback, 6 × 9", bez spadu).

Użycie:
  python make_interior.py --author "Imię Nazwisko"

Specyfikacja KDP (bez bleed): strona PDF = dokładnie format (6 × 9"),
margines wewnętrzny 0.5" (wymagane ≥0.375" do 150 stron), zewnętrzny,
górny i dolny ≥0.4" (wymagane ≥0.25"). Fonty osadzone (DejaVu Sans).
"""
import argparse
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
INK = Color(0.10, 0.13, 0.18)
GRID = Color(0.62, 0.65, 0.70)
HEAD_FILL = Color(0.86, 0.89, 0.93)
SOFT = Color(0.35, 0.38, 0.44)

TRIP_PAGES = 100          # 100 stron × 20 przejazdów = 2000 przejazdów
ROWS_PER_PAGE = 20
EXPENSE_PAGES = 6
NOTES_PAGES = 4

# Kolumny strony przejazdów: (nagłówek w 1–2 liniach, udział szerokości)
TRIP_COLS = [(("Date",), 0.13), (("Destination / purpose",), 0.37), (("Odometer", "start"), 0.15),
             (("Odometer", "end"), 0.15), (("Miles",), 0.10), (("Biz /", "Pers."), 0.10)]
EXPENSE_COLS = [(("Date",), 0.15), (("Description",), 0.37), (("Type",), 0.18),
                (("Amount", "$"), 0.15), (("Biz /", "Pers."), 0.15)]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


class Book:
    def __init__(self, path: Path, author: str, title: str):
        self.c = canvas.Canvas(str(path), pagesize=(W, H), initialFontName="Sans")
        self.c.setTitle(title)
        self.c.setAuthor(author)
        self.c.setCreator("kdp-niche-agent / mileage-log-book")
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
        return y1 - size * 1.9

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


HOW_TO = [
    "Write one line for every trip, on the day you drive it.",
    "Note the odometer reading when you set off and when you arrive, then the miles driven.",
    "Say where you went and why, for example \"Client meeting – Smith & Co, Denver\".",
    "Mark each trip B for business or P for personal.",
    "Add up the miles at the foot of each page, and copy the monthly totals to the annual summary at the back.",
    "Record parking fees, tolls and other vehicle costs on the expense pages, and keep the receipts.",
]
NOTE = ("This logbook is a place to record your driving. It is not tax advice: "
        "ask a tax professional what records you need to keep.")


def build(out: Path, author: str) -> tuple[Path, int]:
    title = "Mileage Log Book for Taxes"
    path = out / "mileage-log-book_6x9_interior.pdf"
    b = Book(path, author, title)
    c = b.c

    # 1 – tytuł
    x0, y0, x1, y1 = b.box()
    mid = (x0 + x1) / 2
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 30)
    c.drawCentredString(mid, y1 - 2.0 * INCH, "MILEAGE")
    c.drawCentredString(mid, y1 - 2.0 * INCH - 36, "LOG BOOK")
    c.setFont("Sans", 12)
    c.setFillColor(SOFT)
    c.drawCentredString(mid, y1 - 2.0 * INCH - 66, "Business and personal driving records")
    b.lines(y0 + 2.6 * INCH, y0 + 0.6 * INCH, step=0.42 * INCH,
            label_rows=["Name:", "Phone:", "Year:", "Vehicle:"])
    b.next()
    # 2 – prawa autorskie
    x0, y0, x1, y1 = b.box()
    c.setFont("Sans", 8.5)
    c.setFillColor(SOFT)
    y = y0 + 70
    for ln in [title, f"Copyright © 2026 {author}. All rights reserved.",
               "No part of this book may be copied without permission."] + wrap(NOTE, "Sans", 8.5, x1 - x0):
        c.drawString(x0, y, ln)
        y -= 12
    b.next()
    # 3 – jak używać
    y = b.heading("How to use this logbook")
    y = b.paragraphs(y, HOW_TO, bullet=True)
    c.setFont("Sans", 9)
    c.setFillColor(SOFT)
    x0, y0, x1, _ = b.box()
    yy = y0 + 40
    for ln in wrap(NOTE, "Sans", 9, x1 - x0):
        c.drawString(x0, yy, ln)
        yy -= 12
    b.next()
    # 4 – dane pojazdu
    y = b.heading("Vehicle information")
    _, y0, _, _ = b.box()
    b.lines(y, y0, step=0.40 * INCH, label_rows=[
        "Make & model:", "Year:", "Color:", "License plate:", "VIN:", "Insurance company:",
        "Policy number:", "Odometer on January 1:", "Odometer on December 31:", "Total miles this year:",
        "Second vehicle:", "License plate:", "Odometer on January 1:", "Odometer on December 31:", None, None])
    b.next()
    # przejazdy
    for _ in range(TRIP_PAGES):
        x0, y0, x1, y1 = b.box()
        c.setFont("Sans-Bold", 9)
        c.setFillColor(INK)
        c.drawString(x0, y1 - 10, "Month: ______________")
        c.drawRightString(x1, y1 - 10, "Vehicle: ______________")
        b.table(TRIP_COLS, ROWS_PER_PAGE, y1 - 22, y0,
                footer="Page total:   Business ________ mi     Personal ________ mi")
        b.next()
    # wydatki
    for _ in range(EXPENSE_PAGES):
        y = b.heading("Parking, tolls & vehicle expenses", size=13)
        _, y0, _, _ = b.box()
        b.table(EXPENSE_COLS, 18, y + 6, y0, footer="Page total:   $ ____________")
        b.next()
    # podsumowanie roczne
    y = b.heading("Annual summary", size=15)
    _, y0, _, _ = b.box()
    cols = [(("Month",), 0.25), (("Business", "miles"), 0.19), (("Personal", "miles"), 0.19),
            (("Total", "miles"), 0.18), (("Expenses", "$"), 0.19)]
    bottom = b.table(cols, 13, y + 6, y0 + 1.1 * INCH, first_col_values=MONTHS + ["Year total"])
    b.paragraphs(bottom - 22, ["Business share of miles: business miles ÷ total miles = ________ %"], size=9.5)
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
