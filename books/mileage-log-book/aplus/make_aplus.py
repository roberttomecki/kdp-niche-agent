#!/usr/bin/env python3
"""Grafiki A+ Content dla Mileage Log Book (ASIN B0HSLRLPXP) – styl okładki: granat, bursztyn, licznik, droga.

Użycie:  python aplus/make_aplus.py
output/aplus/: 1_header_1940x1200.jpg, 2a/2b/2c_square_1200.jpg, 3_banner_1940x600.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK.parent.parent / "tools"))
from aplus_kit import (book_mockup, bullets, caption_square, font, front_cover, page_img,  # noqa: E402
                       shadow_paste, spread, text_lines)

INTERIOR = BOOK / "output" / "mileage-log-book_6x9_interior.pdf"
COVER = BOOK / "output" / "mileage-log-book_6x9_cover.pdf"
OUT = BOOK / "output" / "aplus"
NAVY, INK, TEXT, MUTED, AMBER, LINE = "#22324A", "#16202F", "#F7F7F4", "#B9C4D3", "#F2B33D", "#3A4E6B"


def road(d, x0, x1, y, h=10, dash=70, gap=45):
    x = x0
    while x < x1:
        d.rectangle((x, y, min(x + dash, x1), y + h), fill=AMBER)
        x += dash + gap


def odometer(d, x, y, digits="184362", w=92, h=128, gap=14):
    f = font("ExtraBold", int(h * 0.68))
    for i, ch in enumerate(digits):
        last = i == len(digits) - 1
        bx = x + i * (w + gap)
        d.rounded_rectangle((bx, y, bx + w, y + h), 12, fill=AMBER if last else TEXT)
        d.line((bx + 6, y + h / 2, bx + w - 6, y + h / 2), fill="#d9d9d4" if not last else "#d99a2b", width=2)
        tw = d.textlength(ch, font=f)
        d.text((bx + (w - tw) / 2, y + h * 0.12), ch, font=f, fill=INK)
    d.text((x + len(digits) * (w + gap) + 6, y + h * 0.35), "mi", font=font("Bold", int(h * 0.3)), fill=MUTED)
    return x + len(digits) * (w + gap) + 60


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cover = front_cover(COVER, 6.0, 9.0)
    trip, trip2 = page_img(INTERIOR, 5), page_img(INTERIOR, 6)
    expenses, summary = page_img(INTERIOR, 105), page_img(INTERIOR, 111)

    # 1. nagłówek 1940 × 1200
    im = Image.new("RGB", (1940, 1200), NAVY)
    d = ImageDraw.Draw(im)
    road(d, 0, 1940, 1120)
    mk = book_mockup(cover, 980)
    shadow_paste(im, mk, (130, 80), blur=34, offset=(18, 26), opacity=150)
    x = 130 + mk.width + 120
    y = text_lines(d, x, 150, ["Every trip on", "one line, ready", "for tax time."], font("ExtraBold", 84), TEXT, 98)
    y = bullets(d, x, y + 40, ["Room for 2,000 trips with odometer start and end",
                               "Business or personal marked on every line",
                               "Page totals, expenses and an annual summary"],
                font("Regular", 38), "#E6EAF0", AMBER, 1940 - x - 90, 50)
    d.text((x, y + 20), "6 × 9 in  ·  fits in a glove box", font=font("Bold", 32), fill=MUTED)
    im.save(OUT / "1_header_1940x1200.jpg", quality=92)

    # 2. trzy kwadraty 1200 × 1200
    bg = Image.new("RGB", (1200, 1200), NAVY)
    road(ImageDraw.Draw(bg), 0, 1200, 760, h=8, dash=56, gap=36)
    caption_square(bg, trip, (0.04, 0.03, 0.96, 0.62), "2,000 trips",
                   "Date, destination and purpose, odometer start and end, miles, business or personal.",
                   TEXT, NAVY, "#4A5A72", AMBER).save(OUT / "2a_square_trips_1200.jpg", quality=92)
    caption_square(bg, expenses, (0.04, 0.03, 0.96, 0.62), "Expenses",
                   "Six pages for parking, tolls, fuel and repairs, kept next to your mileage.",
                   TEXT, NAVY, "#4A5A72", AMBER).save(OUT / "2b_square_expenses_1200.jpg", quality=92)
    caption_square(bg, summary, (0.04, 0.03, 0.96, 0.62), "Annual summary",
                   "Month-by-month business and personal miles on a single page.",
                   TEXT, NAVY, "#4A5A72", AMBER).save(OUT / "2c_square_summary_1200.jpg", quality=92)

    # 3. baner 1940 × 600
    im = Image.new("RGB", (1940, 600), NAVY)
    d = ImageDraw.Draw(im)
    road(d, 0, 1940, 548, h=8)
    xe = odometer(d, 90, 120)
    d.text((90, 300), "Log as you drive.", font=font("ExtraBold", 64), fill=TEXT)
    d.text((90, 385), "Have your miles ready when tax season comes.", font=font("Regular", 36), fill=MUTED)
    sp = spread(trip, trip2, 470)
    shadow_paste(im, sp, (1940 - sp.width - 70, 40), blur=22, offset=(10, 16))
    im.save(OUT / "3_banner_1940x600.jpg", quality=92)
    print("\n".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
