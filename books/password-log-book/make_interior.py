#!/usr/bin/env python3
"""Generator wnętrza książki „Large Print Password Log Book” zgodnego z KDP (paperback).

Użycie:
  python make_interior.py --trim 8.5x11 --author "Imię Nazwisko"
  python make_interior.py --trim 6x9    --author "Imię Nazwisko"
  python make_interior.py --all --author "Imię Nazwisko"      # obie wersje

Specyfikacja KDP (interior z bleed):
  - strona PDF = format + 0.125" szerokości i + 0.25" wysokości,
  - spad (bleed) 0.125" od góry, dołu i krawędzi zewnętrznej,
  - margines zewnętrzny/górny/dolny ≥ 0.375", wewnętrzny (gutter) wg liczby stron
    (24–150 str.: 0.375", 151–300: 0.5"; używamy 0.5" dla wygody pisania),
  - wszystkie fonty osadzone (DejaVu Sans, TTF w katalogu fonts/).
Zakładki A–Z są drukowane na zewnętrznej krawędzi i wchodzą w spad,
więc po złożeniu książki tworzą indeks widoczny z boku.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont("Sans", str(HERE / "fonts" / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Sans-Bold", str(HERE / "fonts" / "DejaVuSans-Bold.ttf")))

INCH = 72.0
BLEED = 0.125
GREY_LINE = Color(0.55, 0.55, 0.55)
GREY_LABEL = Color(0.25, 0.25, 0.25)
TAB_DARK = Color(0.12, 0.12, 0.12)
TAB_LIGHT = Color(0.88, 0.88, 0.88)

# Litery i liczba stron na każdą (rzadsze litery dostają mniej miejsca)
SECTIONS = [("A", 4), ("B", 4), ("C", 4), ("D", 4), ("E", 4), ("F", 4), ("G", 4), ("H", 4),
            ("I", 4), ("J", 2), ("K", 2), ("L", 4), ("M", 4), ("N", 4), ("O", 4), ("P", 4),
            ("Q", 2), ("R", 4), ("S", 4), ("T", 4), ("U", 2), ("V", 2), ("W", 4), ("X", 2),
            ("Y", 2), ("Z", 2), ("#", 2)]
FIELDS = ["Website", "Login / Email", "Password", "New password", "New password", "Notes"]


@dataclass
class Spec:
    trim_w: float
    trim_h: float
    entries_per_page: int
    label_size: float     # pt
    letter_size: float    # duża litera nagłówka
    tab_w: float          # szerokość zakładki widoczna po przycięciu (cale)
    tab_font: float
    outer: float = 0.375  # margines zewnętrzny bez zakładki
    top: float = 0.5
    bottom: float = 0.5
    gutter: float = 0.5


SPECS = {
    "8.5x11": Spec(8.5, 11.0, entries_per_page=3, label_size=15, letter_size=40, tab_w=0.42, tab_font=13),
    "6x9": Spec(6.0, 9.0, entries_per_page=2, label_size=13, letter_size=32, tab_w=0.34, tab_font=10),
}


class Book:
    def __init__(self, spec: Spec, path: Path, author: str, title: str):
        self.s = spec
        self.W = (spec.trim_w + BLEED) * INCH
        self.H = (spec.trim_h + 2 * BLEED) * INCH
        self.c = canvas.Canvas(str(path), pagesize=(self.W, self.H), initialFontName="Sans")  # brak nieosadzonej Helvetiki
        self.c.setTitle(title)
        self.c.setAuthor(author)
        self.c.setCreator("kdp-niche-agent / make_interior.py")
        self.page = 1
        self.author = author
        self.title = title

    # --- geometria strony (w punktach) -----------------------------------
    @property
    def recto(self):  # strona nieparzysta = prawa; spad po prawej
        return self.page % 2 == 1

    def trim_box(self):
        """(x0, y0, x1, y1) obszaru po przycięciu."""
        x0 = 0 if self.recto else BLEED * INCH
        return x0, BLEED * INCH, x0 + self.s.trim_w * INCH, BLEED * INCH + self.s.trim_h * INCH

    def content_box(self, with_tab=True):
        x0, y0, x1, y1 = self.trim_box()
        outer = (self.s.outer + (self.s.tab_w if with_tab else 0)) * INCH
        gutter = self.s.gutter * INCH
        if self.recto:
            cx0, cx1 = x0 + gutter, x1 - outer
        else:
            cx0, cx1 = x0 + outer, x1 - gutter
        return cx0, y0 + self.s.bottom * INCH, cx1, y1 - self.s.top * INCH

    def next_page(self):
        self.c.showPage()
        self.page += 1

    # --- elementy -----------------------------------------------------------
    def tab(self, idx: int, label: str):
        """Zakładka na zewnętrznej krawędzi; pozycja zależy od numeru sekcji."""
        n = len(SECTIONS)
        x0, y0, x1, y1 = self.trim_box()
        usable_top = y1 - self.s.top * INCH
        usable_h = (self.s.trim_h - self.s.top - self.s.bottom) * INCH
        h = usable_h / n
        ty = usable_top - (idx + 1) * h
        w = self.s.tab_w * INCH
        if self.recto:
            rx, rw = x1 - w, w + BLEED * INCH  # wchodzi w spad po prawej
        else:
            rx, rw = 0, w + BLEED * INCH       # wchodzi w spad po lewej
        c = self.c
        c.setFillColor(TAB_DARK)
        c.rect(rx, ty + 1, rw, h - 2, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Sans-Bold", self.s.tab_font)
        cx = (x1 - w / 2) if self.recto else (x0 + w / 2)
        c.drawCentredString(cx, ty + h / 2 - self.s.tab_font * 0.36, label)

    def lines_page(self, heading: str):
        cx0, cy0, cx1, cy1 = self.content_box(with_tab=False)
        c = self.c
        c.setFillColor(black)
        c.setFont("Sans-Bold", self.s.label_size + 5)
        c.drawString(cx0, cy1 - self.s.label_size - 5, heading)
        y = cy1 - (self.s.label_size + 5) * 2.2
        step = self.s.label_size * 2.3
        c.setStrokeColor(GREY_LINE)
        c.setLineWidth(0.75)
        while y > cy0:
            c.line(cx0, y, cx1, y)
            y -= step

    def entries_page(self, letter: str, idx: int):
        self.tab(idx, letter)
        cx0, cy0, cx1, cy1 = self.content_box()
        c = self.c
        # nagłówek: duża litera po stronie zewnętrznej
        c.setFillColor(black)
        c.setFont("Sans-Bold", self.s.letter_size)
        head_y = cy1 - self.s.letter_size * 0.8
        if self.recto:
            c.drawRightString(cx1, head_y, letter)
        else:
            c.drawString(cx0, head_y, letter)
        top = head_y - self.s.letter_size * 0.35
        block_h = (top - cy0) / self.s.entries_per_page
        ls = self.s.label_size
        # wszystkie linie do pisania zaczynają się w jednej kolumnie
        col = max(pdfmetrics.stringWidth(f + ":", "Sans-Bold", ls) for f in FIELDS) + 10
        for e in range(self.s.entries_per_page):
            by = top - e * block_h
            row_h = (block_h - ls * 0.9) / len(FIELDS)
            for f, field in enumerate(FIELDS):
                base = by - (f + 1) * row_h
                c.setFillColor(black if f < 3 else GREY_LABEL)  # główne pola mocniej
                c.setFont("Sans-Bold", ls)
                c.drawString(cx0, base + 3, field + ":")
                c.setStrokeColor(GREY_LINE)
                c.setLineWidth(0.75)
                c.line(cx0 + col, base + 1, cx1, base + 1)
            if e < self.s.entries_per_page - 1:  # separator między wpisami
                sep_y = by - block_h + ls * 0.45
                c.setStrokeColor(black)
                c.setLineWidth(1.6)
                c.line(cx0, sep_y, cx1, sep_y)

    def text_page(self, heading: str, paragraphs: list[str], centered=False, size=None):
        cx0, cy0, cx1, cy1 = self.content_box(with_tab=False)
        c = self.c
        size = size or self.s.label_size
        c.setFillColor(black)
        y = cy1 - (size + 6) * 1.5
        c.setFont("Sans-Bold", size + 6)
        if centered:
            c.drawCentredString((cx0 + cx1) / 2, y, heading)
        else:
            c.drawString(cx0, y, heading)
        y -= (size + 6) * 1.6
        c.setFont("Sans", size)
        for p in paragraphs:
            for line in wrap(p, "Sans", size, cx1 - cx0):
                if centered:
                    c.drawCentredString((cx0 + cx1) / 2, y, line)
                else:
                    c.drawString(cx0, y, line)
                y -= size * 1.45
            y -= size * 0.7

    def title_page(self):
        x0, y0, x1, y1 = self.trim_box()
        c, mid = self.c, (x0 + x1) / 2
        big = self.s.letter_size
        c.setFillColor(black)
        c.setFont("Sans-Bold", big)
        y = y1 - (self.s.trim_h * 0.30) * INCH
        for line in ["PASSWORD", "LOG BOOK"]:
            c.drawCentredString(mid, y, line)
            y -= big * 1.15
        c.setFont("Sans", self.s.label_size + 2)
        c.drawCentredString(mid, y - 10, "Large Print  •  Alphabetical Tabs")
        # pole „This book belongs to”
        c.setFont("Sans-Bold", self.s.label_size)
        yb = y0 + (self.s.trim_h * 0.28) * INCH
        c.drawCentredString(mid, yb + 30, "This book belongs to:")
        c.setStrokeColor(GREY_LINE)
        c.setLineWidth(0.75)
        c.line(x0 + 1.0 * INCH, yb, x1 - 1.0 * INCH, yb)

    def copyright_page(self):
        cx0, cy0, cx1, cy1 = self.content_box(with_tab=False)
        c = self.c
        c.setFillColor(GREY_LABEL)
        c.setFont("Sans", 9)
        lines = [self.title, f"Copyright © 2026 {self.author}. All rights reserved.",
                 "No part of this publication may be reproduced without permission.",
                 "Keep this book in a safe, private place."]
        y = cy0 + 60
        for ln in lines:
            c.drawString(cx0, y, ln)
            y -= 13

    def save(self):
        self.c.save()


def wrap(text, font, size, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


HOW_TO = [
    "Each letter has its own section. Use the black tabs on the edge of the pages to find it quickly.",
    "Write each website under the first letter of its name (for example, \"Amazon\" goes under A). "
    "Websites that start with a number go under #.",
    "When you change a password, write the new one on a \"New password\" line instead of erasing "
    "the old one.",
    "Use a pencil if you like - it makes corrections easy.",
]
TIPS = [
    "Use a different password for every website.",
    "Longer is stronger: a short sentence you can remember works well.",
    "Never share your passwords by phone or email. Your bank will never ask for them.",
    "Turn on two-step verification where it is offered.",
    "Do not label the outside of this book \"passwords\" and keep it in a safe place at home.",
]


def build(trim: str, out_dir: Path, author: str):
    spec = SPECS[trim]
    title = "Large Print Password Log Book"
    path = out_dir / f"password-log-book_{trim}_interior.pdf"
    b = Book(spec, path, author, title)

    b.title_page(); b.next_page()                                   # 1
    b.copyright_page(); b.next_page()                               # 2
    b.text_page("How to Use This Book", HOW_TO); b.next_page()      # 3
    b.text_page("Password Safety Tips", ["• " + t for t in TIPS]); b.next_page()  # 4
    for heading in ["Email Accounts", "Home Internet & Wi-Fi"]:    # 5–6
        b.lines_page(heading); b.next_page()
    for idx, (letter, pages) in enumerate(SECTIONS):
        for _ in range(pages):
            b.entries_page(letter, idx); b.next_page()
    notes = 6
    for i in range(notes):
        b.lines_page("Notes")
        if i < notes - 1:
            b.next_page()
    total = b.page
    if total % 2:  # KDP i tak zaokrągla do parzystej – dodajmy stronę Notes sami
        b.next_page(); b.lines_page("Notes"); total += 1
    b.save()
    return path, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trim", choices=SPECS, default="8.5x11")
    ap.add_argument("--all", action="store_true", help="wygeneruj wszystkie formaty")
    ap.add_argument("--author", required=True, help="imię i nazwisko lub nazwa wydawnictwa na stronie z prawami")
    ap.add_argument("--out", default=str(HERE / "output"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for t in (SPECS if a.all else [a.trim]):
        p, n = build(t, out, a.author)
        print(f"{p}  ({n} stron)")


if __name__ == "__main__":
    main()
