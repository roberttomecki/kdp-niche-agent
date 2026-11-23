#!/usr/bin/env python3
"""Grafiki A+ Content (sekcja „From the Publisher”) dla Deer Hunting Log Book.

Użycie:  python aplus/make_aplus.py [--variant orange|green]
Wymaga: gotowych PDF-ów w output/ (wnętrze i okładka) oraz pdftoppm (poppler-utils).

Pliki (output/aplus/):
  1_header_1940x1200.jpg       – moduł „Standard Image Header With Text” (970 × 600, ×2)
  2a/2b/2c_square_1200.jpg     – moduł „Standard Three Images & Text” (600 × 600, ×2)
  3_banner_1940x600.jpg        – moduł „Standard Image & Light/Dark Text Overlay” albo osobny baner (970 × 300, ×2)
Styl jak okładka „Contour Vigil”: mapa poziomic, kość, pomarańcz sygnałowy; prawdziwe strony książki zamiast zdjęć.
"""
import argparse
import importlib.util
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
OUT = BOOK / "output"

spec = importlib.util.spec_from_file_location("cover", BOOK / "cover" / "make_cover.py")
cov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cov)                       # kroje, paleta, poziomice, ilustracja jelenia

PPI = 100                                          # px na „cal” mapy tła


def rgb(col):
    return tuple(int(round(v * 255)) for v in (col.red, col.green, col.blue))


def render_pdf_page(pdf: Path, page: int, dpi: int) -> Image.Image:
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(page), "-l", str(page),
                        "-singlefile", str(pdf), f"{d}/p"], check=True)
        return Image.open(f"{d}/p.png").convert("RGB")


def contour_bg(w, h, shift=0.0, text=None) -> Image.Image:
    """Tło: mapa poziomic jak na okładce (wektorowo przez reportlab → raster)."""
    W, H = w / PPI, h / PPI
    segs = cov.contours(W, H, shift, np.linspace(-0.18, 1.26, 49))
    with tempfile.TemporaryDirectory() as d:
        pdf = f"{d}/bg.pdf"
        c = canvas.Canvas(pdf, pagesize=(w, h), initialFontName="Mono")
        c.setFillColor(cov.GROUND)
        c.rect(0, 0, w, h, stroke=0, fill=1)
        c.setLineCap(1); c.setLineJoin(1)
        for i, lev in enumerate(segs):
            idx = i % 5 == 0
            c.setStrokeColor(cov.INDEX if idx else cov.CONTOUR)
            c.setLineWidth(1.6 if idx else 0.8)
            for s in lev:
                if len(s) < 3:
                    continue
                p = c.beginPath()
                p.moveTo(*(s[0] * PPI))
                for x, y in s[1:]:
                    p.lineTo(x * PPI, y * PPI)
                c.drawPath(p, stroke=1, fill=0)
        if text:
            text(c)
        c.showPage(); c.save()
        subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", pdf, f"{d}/bg"], check=True)
        return Image.open(f"{d}/bg.png").convert("RGB")


def paste_shadow(base: Image.Image, img: Image.Image, xy, blur=18, offset=(10, 14), opacity=150):
    x, y = xy
    sh = Image.new("L", (img.width + 4 * blur, img.height + 4 * blur), 0)
    ImageDraw.Draw(sh).rectangle((2 * blur, 2 * blur, 2 * blur + img.width, 2 * blur + img.height), fill=opacity)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    black = Image.new("RGB", sh.size, (8, 12, 9))
    base.paste(black, (x - 2 * blur + offset[0], y - 2 * blur + offset[1]), sh)
    base.paste(img, (x, y))


def cover_front(variant: str, height: int) -> Image.Image:
    name = "deer-hunting-log-book_6x9_cover" + ("_orange" if variant == "orange" else "") + ".pdf"
    im = render_pdf_page(OUT / name, 1, 220)
    W, H = im.size
    total_w = 2 * cov.BLEED + 2 * cov.TW + 110 * cov.PAPER
    x0 = int(W * (cov.BLEED + cov.TW + 110 * cov.PAPER) / total_w)
    bx = int(W * cov.BLEED / total_w); by = int(H * cov.BLEED / (cov.TH + 2 * cov.BLEED))
    front = im.crop((x0, by, W - bx, H - by))
    return front.resize((int(height * front.width / front.height), height), Image.LANCZOS)


def page_img(page: int, height: int, crop=None) -> Image.Image:
    im = render_pdf_page(OUT / "deer-hunting-log-book_6x9_interior.pdf", page, 300)
    if crop:                                       # crop w ułamkach strony (x0, y0, x1, y1), y od góry
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    return im.resize((int(height * im.width / im.height), height), Image.LANCZOS)


def header(variant: str, path: Path):
    w, h = 1940, 1200
    tx = 1455

    def text(c):
        c.setFillColor(cov.BONE)
        size = 58
        c.setFont("Park", size)
        y = h - 330
        for ln in ["EVERY SIT,", "ON RECORD."]:
            c.drawString(tx, y, ln)
            y -= size * 1.08
        c.setStrokeColor(cov.BLAZE); c.setLineWidth(6)
        c.line(tx, y + 12, tx + 120, y + 12)
        c.setFont("Jura", 27)
        y -= 50
        for ln in ["Wind, weather and moon", "for every hunt. The deer", "you saw, the shot you", "took, the stand that", "paid off."]:
            c.drawString(tx, y, ln)
            y -= 38
    bg = contour_bg(w, h, shift=-3.0, text=text)
    front = cover_front(variant, 980)
    page = page_img(12, 900)
    paste_shadow(bg, page, (800, 150))
    paste_shadow(bg, front, (120, 110), blur=22, offset=(14, 18), opacity=170)
    bg.save(path, quality=92)


def square(page: int, crop, path: Path, shift: float):
    s = 1200
    bg = contour_bg(s, s, shift=shift)
    card = page_img(page, 1000, crop)
    if card.width > 1040:
        card = card.resize((1040, int(card.height * 1040 / card.width)), Image.LANCZOS)
    paste_shadow(bg, card, ((s - card.width) // 2, (s - card.height) // 2))
    bg.save(path, quality=92)


def banner(path: Path):
    w, h = 1940, 600
    items = ["80 hunt pages: wind compass, weather, moon", "Deer-seen tables: bucks, does, fawns",
             "8 harvest records with a deer to mark the hit", "Stands, trail cameras, property maps",
             "Season summaries, year after year"]

    def text(c):
        c.setFillColor(cov.BONE)
        c.setFont("Park", 54)
        c.drawString(110, h - 120, "BUILT FOR THE STAND")
        c.setStrokeColor(cov.BLAZE); c.setLineWidth(6)
        c.line(110, h - 152, 230, h - 152)
        c.setFont("Jura", 30)
        y = h - 225
        for it in items:
            c.setFillColor(cov.BLAZE)
            c.rect(110, y + 3, 13, 13, stroke=0, fill=1)
            c.setFillColor(cov.BONE)
            c.drawString(145, y, it)
            y -= 62
    bg = contour_bg(w, h, shift=4.0, text=text)
    deer = cov.deer_layer(cov.BONE, cov.GROUND, 0.8)
    dh = 540
    deer = deer.resize((int(dh * deer.width / deer.height), dh), Image.LANCZOS)
    bg.paste(deer, (w - deer.width - 120, (h - dh) // 2 + 10), deer)
    bg.save(path, quality=92)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["orange", "green"], default="orange",
                    help="która okładka jest wgrana do KDP (tła A+ są zawsze w zieleni)")
    a = ap.parse_args()
    cov.use_palette("green")                       # tło A+ zawsze ciemnozielone z kością
    out = OUT / "aplus"
    out.mkdir(parents=True, exist_ok=True)
    header(a.variant, out / f"1_header_1940x1200_{a.variant}.jpg")
    cov.use_palette("green")
    square(12, (0.0, 0.0, 1.0, 0.62), out / "2a_square_hunt_1200.jpg", -1.0)
    square(92, (0.0, 0.535, 1.0, 1.0), out / "2b_square_harvest_1200.jpg", 2.0)
    square(6, (0.0, 0.0, 1.0, 0.40), out / "2c_square_stands_1200.jpg", 5.0)
    banner(out / "3_banner_1940x600.jpg")
    for p in sorted(out.iterdir()):
        im = Image.open(p)
        print(f"{p.name}: {im.size[0]}×{im.size[1]}, {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
