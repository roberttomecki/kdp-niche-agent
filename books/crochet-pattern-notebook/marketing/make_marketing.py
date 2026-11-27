#!/usr/bin/env python3
"""Pakiet marketingowy „Crochet Pattern Notebook” – seria Golden Stitch.

Użycie:  python marketing/make_marketing.py
Wymaga gotowych PDF-ów w output/ (wnętrze i okładka) oraz pdftoppm.

output/marketing/
  aplus_1_header_1940x1200.jpg      – A+ „Standard Image Header With Text” (970 × 600, ×2)
  aplus_2a/2b/2c_square_1200.jpg    – A+ „Standard Three Images & Text” (300 × 300 i więcej)
  aplus_3_banner_1940x600.jpg       – A+ „Standard Image & Dark Text Overlay” (970 × 300, ×2)
  mockup_cover_2000.jpg / mockup_spread_2400x1600.jpg – mockupy do A+, sklepu, social mediów
  pin_1/2/3_1000x1500.jpg           – piny Pinterest (2:3)
Tła to ta sama sztuka generatywna Golden Stitch (inne seedy), prawdziwe strony książki zamiast zdjęć.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
SERIES = BOOK.parent.parent / "series" / "golden-stitch"
sys.path.insert(0, str(SERIES))
from render import render_many  # noqa: E402

OUT = BOOK / "output" / "marketing"
INTERIOR = BOOK / "output" / "crochet-pattern-notebook_8.5x11_interior.pdf"
COVER = BOOK / "output" / "crochet-pattern-notebook_8.5x11_cover.pdf"
F = SERIES / "fonts"

PLUM, CREAM, AMBER, CORAL, TEAL = "#2a1730", "#f6ead6", "#f2a03d", "#e2574c", "#3fa39a"
YARNS = [AMBER, CORAL, "#f6e7cf", TEAL]
MUTED = "#6b4a6e"


def font(name, size):
    return ImageFont.truetype(str(F / f"{name}.ttf"), size)


def page_img(pdf, page, dpi=150):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(page), "-l", str(page), "-singlefile",
                        str(pdf), f"{d}/p"], check=True)
        return Image.open(f"{d}/p.png").convert("RGB")


def front_cover(dpi=200):
    im = page_img(COVER, 1, dpi)
    spine = 106 * 0.002252
    x0 = round((0.125 + 8.5 + spine) * dpi)
    return im.crop((x0, round(0.125 * dpi), x0 + round(8.5 * dpi), round(11.125 * dpi)))


def shadow_paste(base, img, xy, blur=28, offset=(14, 22), opacity=130):
    x, y = xy
    pad = blur * 3
    sh = Image.new("L", (img.width + 2 * pad, img.height + 2 * pad), 0)
    ImageDraw.Draw(sh).rectangle((pad, pad, pad + img.width, pad + img.height), fill=opacity)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    dark = Image.new("RGB", sh.size, (10, 4, 9))
    base.paste(dark, (x - pad + offset[0], y - pad + offset[1]), sh)
    base.paste(img, (x, y))


def book_mockup(cover, height):
    """Okładka z grubością stron po prawej i miękkim połyskiem – „stojąca” książka."""
    w = round(cover.width * height / cover.height)
    cv = cover.resize((w, height), Image.LANCZOS)
    edge = max(6, w // 60)
    out = Image.new("RGBA", (w + edge, height), (0, 0, 0, 0))
    pages = Image.new("RGB", (edge, height - 8), "#efe9e0")
    d = ImageDraw.Draw(pages)
    for i in range(0, edge, 2):
        d.line((i, 0, i, height), fill="#ddd5ca")
    out.paste(pages, (w, 4))
    out.paste(cv, (0, 0))
    # grzbietowy cień i połysk
    ov = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(int(w * 0.05)):
        a = int(70 * (1 - i / (w * 0.05)))
        od.line((i, 0, i, height), fill=(0, 0, 0, a))
    for i in range(int(w * 0.25)):
        a = int(26 * (1 - abs(i - w * 0.125) / (w * 0.125)))
        od.line((int(w * 0.09) + i, 0, int(w * 0.09) + i, height), fill=(255, 255, 255, max(0, a)))
    out.alpha_composite(ov, (0, 0))
    return out


def paste_rgba_shadow(base, img, xy, blur=30, offset=(18, 26), opacity=150):
    x, y = xy
    pad = blur * 3
    sh = Image.new("L", (img.width + 2 * pad, img.height + 2 * pad), 0)
    sh.paste(img.split()[-1].point(lambda v: opacity if v > 0 else 0), (pad, pad))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.paste(Image.new("RGB", sh.size, (10, 4, 9)), (x - pad + offset[0], y - pad + offset[1]), sh)
    base.paste(img, (x, y), img)


def spread(left, right, height):
    """Rozkładówka: dwie strony z cieniem przy grzbiecie."""
    w = round(left.width * height / left.height)
    L, R = left.resize((w, height), Image.LANCZOS), right.resize((w, height), Image.LANCZOS)
    s = Image.new("RGB", (w * 2, height), "white")
    s.paste(L, (0, 0))
    s.paste(R, (w, 0))
    ov = Image.new("RGBA", s.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    g = int(w * 0.09)
    for i in range(g):
        a = int(85 * (1 - i / g) ** 2)
        od.line((w - i, 0, w - i, height), fill=(40, 20, 40, a))
        od.line((w + i, 0, w + i, height), fill=(40, 20, 40, a))
    return Image.alpha_composite(s.convert("RGBA"), ov).convert("RGB")


def text_block(d, x, y, lines, fnt, fill, lead):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lead
    return y


def wrap(d, text, fnt, width):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=fnt) <= width:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def chain(d, x0, x1, y, link, col, lw):
    n = max(1, int((x1 - x0) / link))
    step = (x1 - x0) / n
    for i in range(n):
        cx = x0 + step * (i + 0.5)
        d.ellipse((cx - step * 0.52, y - link * 0.24, cx + step * 0.52, y + link * 0.24), outline=col, width=lw)


def phi_mark(d, x, y, r, col, lw):
    d.ellipse((x - r * 0.78, y - r * 0.62, x + r * 0.78, y + r * 0.62), outline=col, width=lw)
    d.line((x, y - r * 1.15, x, y + r * 1.15), fill=col, width=lw)


def series_tag(d, x, y, col, size=26):
    phi_mark(d, x + 12, y + size * 0.55, size * 0.62, col, max(2, size // 9))
    f = font("Jost-Bold", size)
    xx = x + 34
    for ch in "GOLDEN STITCH NOTEBOOKS":
        d.text((xx, y), ch, font=f, fill=col)
        xx += d.textlength(ch, font=f) + size * 0.2


def caption_card(img, title, sub, size=1200):
    """Kwadrat A+: strona książki na tle sztuki + kremowy pas z podpisem (styl okładki)."""
    base = img
    band_h = round(size / 1.618 ** 2 * 0.9)
    d = ImageDraw.Draw(base)
    d.rectangle((0, size - band_h, size, size), fill=CREAM)
    chain(d, 0, size, size - band_h, 34, AMBER, 4)
    ft, fs = font("Fraunces-ExtraBold", 66), font("Jost-Regular", 34)
    d.text((60, size - band_h + 52), title, font=ft, fill=PLUM)
    text_block(d, 60, size - band_h + 140, wrap(d, sub, fs, size - 120), fs, MUTED, 46)
    return base


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    art = OUT / "art"
    art.mkdir(exist_ok=True)
    base = {"jitter": 0.18, "armsF": 21, "roundsF": True, "tail": False, "grain": 1.0, "unitPx": 200,
            "ground": PLUM, "shade": "#12070f", "yarns": YARNS}
    jobs = [
        (dict(base, seed=21, W=1940, H=1200, cx=1500, cy=470, count=1100, spacing=24, tail=True, tailAngle=3.0), art / "hdr.png"),
        (dict(base, seed=22, W=1200, H=1200, cx=960, cy=120, count=900, spacing=26), art / "sq.png"),
        (dict(base, seed=23, W=1940, H=600, cx=1960, cy=300, count=650, spacing=22), art / "ban.png"),
        (dict(base, seed=24, W=1000, H=1500, cx=760, cy=300, count=900, spacing=21, tail=True, tailAngle=2.6), art / "pin1.png"),
        (dict(base, seed=25, W=1000, H=1500, cx=180, cy=1320, count=900, spacing=21), art / "pin2.png"),
        (dict(base, seed=26, W=1000, H=1500, cx=880, cy=120, count=900, spacing=21), art / "pin3.png"),
        (dict(base, seed=27, W=2400, H=1600, cx=2050, cy=1350, count=1300, spacing=28), art / "spr.png"),
        (dict(base, seed=28, W=2000, H=2000, cx=1500, cy=520, count=1300, spacing=30, tail=True, tailAngle=2.8), art / "mock.png"),
    ]
    render_many(jobs)
    A = {p.stem: Image.open(p).convert("RGB") for _, p in jobs}
    cover = front_cover()
    card, tracker = page_img(INTERIOR, 10), page_img(INTERIOR, 11)
    abbr, charts, graph, idx = page_img(INTERIOR, 3), page_img(INTERIOR, 4), page_img(INTERIOR, 90), page_img(INTERIOR, 8)

    # --- A+ 1: nagłówek 1940 × 1200 ----------------------------------------------------
    im = A["hdr"].copy()
    d = ImageDraw.Draw(im)
    mk = book_mockup(cover, 1000)
    paste_rgba_shadow(im, mk, (110, 100))
    x = 110 + mk.width + 110
    series_tag(d, x, 210, AMBER, 26)
    f1 = font("Fraunces-SemiBold", 70)
    y = text_block(d, x, 270, ["Every stitch", "counted.", "Every project", "remembered."], f1, CREAM, 84)
    # półprzezroczysty panel pod tekstem, żeby był czytelny na spirali
    im2 = A["hdr"].copy()
    panel = Image.new("RGBA", im2.size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((x - 50, 170, 1880, 1040), 26, fill=(42, 23, 48, 225))
    im2 = Image.alpha_composite(im2.convert("RGBA"), panel).convert("RGB")
    paste_rgba_shadow(im2, mk, (110, 100))
    d = ImageDraw.Draw(im2)
    series_tag(d, x, 210, AMBER, 26)
    y = text_block(d, x, 270, ["Every stitch", "counted.", "Every project", "remembered."], f1, CREAM, 84)
    fb = font("Jost-Regular", 34)
    y += 30
    for ln in ["40 two-page project spreads", "Row counter, gauge & yarn tracker", "US / UK charts and chart paper"]:
        d.ellipse((x, y + 14, x + 14, y + 28), fill=AMBER)
        d.text((x + 32, y), ln, font=fb, fill="#e9dccb")
        y += 52
    im2.save(OUT / "aplus_1_header_1940x1200.jpg", quality=92)

    # --- A+ 2: trzy kwadraty 1200 × 1200 ----------------------------------------------
    def square(page, crop_box, title, sub, name):
        im = A["sq"].copy()
        pg = page.crop(crop_box)
        scale = 980 / pg.width
        pg = pg.resize((980, round(pg.height * scale)), Image.LANCZOS)
        band_h = round(1200 / 1.618 ** 2 * 0.9)
        avail = 1200 - band_h - 60
        if pg.height > avail:
            pg = pg.crop((0, 0, pg.width, avail))
        shadow_paste(im, pg, (110, 60))
        caption_card(im, title, sub).save(OUT / name, quality=92)

    W1, H1 = card.size   # 150 dpi: 1275 × 1650
    square(card, (40, 40, W1 - 40, int(H1 * 0.62)), "Project card",
           "Pattern source, yarn & dye lot, hook, gauge, size and stitches – all in one place.", "aplus_2a_square_project_1200.jpg")
    square(tracker, (40, 40, W1 - 40, int(H1 * 0.55)), "Row counter",
           "Tick off rows 1–60 as you go, with 24 lines of instructions per project.", "aplus_2b_square_rows_1200.jpg")
    square(charts, (40, 40, W1 - 40, int(H1 * 0.62)), "Quick reference",
           "US/UK abbreviations, hook sizes, yarn weights, plus 10 pages of chart paper.", "aplus_2c_square_reference_1200.jpg")

    # --- A+ 3: baner 1940 × 600 ----------------------------------------------------------
    im = A["ban"].copy()
    sp = spread(card, tracker, 500)
    shadow_paste(im, sp, (60, 50))
    d = ImageDraw.Draw(im)
    x = 60 + sp.width + 70
    d.text((x, 150), "40 project", font=font("Fraunces-ExtraBold", 64), fill=CREAM)
    d.text((x, 228), "spreads", font=font("Fraunces-ExtraBold", 64), fill=CREAM)
    text_block(d, x, 330, ["Card on the left,", "rows on the right."], font("Jost-Regular", 32), "#e9dccb", 44)
    im.save(OUT / "aplus_3_banner_1940x600.jpg", quality=92)

    # --- mockupy -------------------------------------------------------------------------
    im = A["mock"].copy()
    mk = book_mockup(cover, 1640)
    paste_rgba_shadow(im, mk, (330, 170), blur=40, offset=(26, 34))
    im.save(OUT / "mockup_cover_2000.jpg", quality=92)
    im = A["spr"].copy()
    sp = spread(card, tracker, 1360)
    shadow_paste(im, sp, ((2400 - sp.width) // 2, 120), blur=36, offset=(20, 30))
    im.save(OUT / "mockup_spread_2400x1600.jpg", quality=92)

    # --- piny Pinterest 1000 × 1500 -------------------------------------------------------
    def pin_band(im, lines, sub, top_y):
        d = ImageDraw.Draw(im)
        d.rectangle((0, top_y, 1000, 1500), fill=CREAM)
        chain(d, 0, 1000, top_y, 30, AMBER, 4)
        f = font("Fraunces-ExtraBold", 78)
        y = text_block(d, 60, top_y + 50, lines, f, PLUM, 88)
        text_block(d, 60, y + 16, wrap(d, sub, font("Jost-Regular", 34), 880), font("Jost-Regular", 34), MUTED, 46)
        series_tag(d, 60, 1500 - 80, PLUM, 22)
        return im

    im = A["pin1"].copy()
    mk = book_mockup(cover, 860)
    paste_rgba_shadow(im, mk, (200, 80))
    pin_band(im, ["Never lose a", "crochet pattern"], "Hook, yarn, gauge and every row you changed – written down for next time.", 1010)
    im.save(OUT / "pin_1_never-lose-a-pattern_1000x1500.jpg", quality=92)

    im = A["pin2"].copy()
    sp = spread(card, tracker, 560)
    sp = sp.resize((900, round(sp.height * 900 / sp.width)), Image.LANCZOS)
    shadow_paste(im, sp, (50, 200))
    d = ImageDraw.Draw(im)
    d.text((60, 70), "Look inside", font=font("Fraunces-ExtraBold", 74), fill=CREAM)
    pin_band(im, ["40 project", "spreads"], "Project card on the left, row counter on the right. 106 pages, 8.5 × 11 in.", 1010)
    im.save(OUT / "pin_2_look-inside_1000x1500.jpg", quality=92)

    im = A["pin3"].copy()
    pg = abbr.crop((40, 40, abbr.width - 40, int(abbr.height * 0.6)))
    pg = pg.resize((820, round(pg.height * 820 / pg.width)), Image.LANCZOS)
    shadow_paste(im, pg, (90, 120))
    pin_band(im, ["US or UK", "crochet terms?"], "Both are inside, side by side – plus hook sizes and yarn weights.", 1010)
    im.save(OUT / "pin_3_us-uk-terms_1000x1500.jpg", quality=92)

    for _, p in jobs:
        p.unlink()
    art.rmdir()
    print("\n".join(sorted(str(p.name) for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
