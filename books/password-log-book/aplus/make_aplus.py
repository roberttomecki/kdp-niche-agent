#!/usr/bin/env python3
"""Grafiki A+ Content dla Password Log Book Large Print (ASIN B0HSCT2JS5) – styl okładki: zieleń, mosiądz, zakładki A–Z.

Użycie:  python aplus/make_aplus.py
output/aplus/: 1_header_1940x1200.jpg, 2a/2b/2c_square_1200.jpg, 3_banner_1940x600.jpg
"""
import string
import sys
from pathlib import Path

from PIL import Image, ImageDraw

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK.parent.parent / "tools"))
from aplus_kit import (book_mockup, bullets, caption_square, font, front_cover, page_img,  # noqa: E402
                       shadow_paste, spread, text_lines)

INTERIOR = BOOK / "output" / "password-log-book_8.5x11_interior.pdf"
COVER = BOOK / "output" / "password-log-book_8.5x11_cover.pdf"
OUT = BOOK / "output" / "aplus"
GROUND, TAB_A, TAB_B, TAB_INK, BRASS, BRASS_INK = "#1F4A40", "#2B5E52", "#25554A", "#CFE0D8", "#E3B341", "#1A2E28"
TEXT, MUTED, PAPER = "#FBFBF8", "#BFD3CA", "#F6F4EE"
LETTERS = list(string.ascii_uppercase) + ["#"]


def tab_strip(d, x, y, h, w=70, active="P", out=26):
    """Pionowy pasek zakładek A–Z jak na okładce; aktywna litera wysunięta w kolorze mosiądzu."""
    step = h / len(LETTERS)
    f = font("Bold", int(step * 0.5))
    for i, ch in enumerate(LETTERS):
        y0 = y + i * step
        act = ch == active
        fill = BRASS if act else (TAB_A if i % 2 else TAB_B)
        x0 = x - out if act else x
        d.rounded_rectangle((x0, y0 + 2, x + w, y0 + step - 2), 6, fill=fill)
        d.text((x0 + 12, y0 + step * 0.22), ch, font=f, fill=BRASS_INK if act else TAB_INK)


def fore_edge(size=1200):
    """Kwadrat: zamknięta książka widziana od krawędzi – każda litera to czarny znacznik na swojej wysokości,
    a sekcje idą po kolei w głąb bloku stron, więc znaczniki układają się w schodki."""
    im = Image.new("RGB", (size, size), GROUND)
    d = ImageDraw.Draw(im)
    bx0, bx1, by0, by1 = 250, 830, 60, 760
    d.rectangle((bx0, by0, bx1, by1), fill=PAPER)
    for xx in range(bx0, bx1, 4):
        d.line((xx, by0, xx, by1), fill="#e8e4da")
    n = len(LETTERS)
    step_y = (by1 - by0) / n
    step_x = (bx1 - bx0) / n
    f = font("Bold", 21)
    for i, ch in enumerate(LETTERS):
        y0 = by0 + i * step_y
        x0 = bx0 + i * step_x
        d.rectangle((x0, y0 + 1, x0 + step_x, y0 + step_y - 1), fill="#1b1b1b")
        d.text((bx1 + 24 + (i % 2) * 26, y0 + step_y * 0.12), ch, font=f, fill=TAB_INK)
    band_h = round(size * 0.34)
    d.rectangle((0, size - band_h, size, size), fill=TEXT)
    d.rectangle((0, size - band_h, size, size - band_h + 10), fill=BRASS)
    d.text((60, size - band_h + 50), "A–Z on the edge", font=font("ExtraBold", 66), fill=GROUND)
    text_lines(d, 60, size - band_h + 140, ["Each letter is printed to the page edge – no cut tabs.", "The book falls open near the right letter."],
               font("Regular", 36), "#4F6B62", 48)
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cover = front_cover(COVER, 8.5, 11.0)
    email, wifi, a1, a2 = (page_img(INTERIOR, p) for p in (5, 6, 7, 8))

    # 1. nagłówek 1940 × 1200
    im = Image.new("RGB", (1940, 1200), GROUND)
    d = ImageDraw.Draw(im)
    tab_strip(d, 1940 - 70, 40, 1120)
    mk = book_mockup(cover, 1000)
    shadow_paste(im, mk, (120, 90), blur=34, offset=(18, 26), opacity=150)
    x = 120 + mk.width + 110
    y = text_lines(d, x, 150, ["Every login in", "one place you can", "actually read."], font("ExtraBold", 80), TEXT, 94)
    y = bullets(d, x, y + 40, ["Large print: everything 16 pt or bigger",
                               "A–Z index printed on the page edge",
                               "Room for 270 websites, with spare lines for new passwords"],
                font("Regular", 38), "#E4EEE9", BRASS, 1940 - x - 170, 50)
    d.text((x, y + 20), "8.5 × 11 in  ·  102 pages", font=font("Bold", 32), fill=MUTED)
    im.save(OUT / "1_header_1940x1200.jpg", quality=92)

    # 2. trzy kwadraty 1200 × 1200
    bg = Image.new("RGB", (1200, 1200), GROUND)
    caption_square(bg, a1, (0.0, 0.03, 1.0, 0.5), "Big, clear print",
                   "Wide lines to write on and two spare lines when a password changes.",
                   TEXT, GROUND, "#4F6B62", BRASS).save(OUT / "2a_square_large_print_1200.jpg", quality=92)
    fore_edge().save(OUT / "2b_square_az_edge_1200.jpg", quality=92)
    caption_square(bg, email, (0.05, 0.02, 0.95, 0.55), "Email & Wi-Fi",
                   "Separate pages for email accounts and your home internet details.",
                   TEXT, GROUND, "#4F6B62", BRASS).save(OUT / "2c_square_email_wifi_1200.jpg", quality=92)

    # 3. baner 1940 × 600
    im = Image.new("RGB", (1940, 600), GROUND)
    d = ImageDraw.Draw(im)
    sp = spread(a2, a1, 500)
    shadow_paste(im, sp, (70, 50), blur=22, offset=(10, 16))
    x = 70 + sp.width + 90
    d.text((x, 160), "Find any login", font=font("ExtraBold", 66), fill=TEXT)
    d.text((x, 240), "in seconds.", font=font("ExtraBold", 66), fill=BRASS)
    text_lines(d, x, 350, ["Open at the letter and read", "every line in large print."], font("Regular", 36), MUTED, 48)
    tab_strip(d, 1940 - 60, 20, 560, w=60, out=20)
    im.save(OUT / "3_banner_1940x600.jpg", quality=92)
    print("\n".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
