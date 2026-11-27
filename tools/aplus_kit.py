"""Wspólne narzędzia do grafik A+ Content i materiałów promocyjnych KDP.

Prawdziwe strony książki (z PDF) zamiast zdjęć, mockup okładki z grubością stron, rozkładówka z cieniem grzbietu.
Rozmiary modułów A+ (×2 dla ostrości): nagłówek 1940 × 1200, kwadrat 1200 × 1200, baner 1940 × 600.
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).resolve().parent / "fonts"


def font(weight: str, size: int):
    """weight: Regular | Bold | ExtraBold (Atkinson Hyperlegible Next, OFL)."""
    return ImageFont.truetype(str(FONTS / f"AtkinsonHyperlegibleNext-{weight}.ttf"), size)


def page_img(pdf, page, dpi=150):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(page), "-l", str(page), "-singlefile",
                        str(pdf), f"{d}/p"], check=True)
        return Image.open(f"{d}/p.png").convert("RGB")


def front_cover(cover_pdf, trim_w, trim_h, bleed=0.125, dpi=200):
    """Przód okładki (bez spadu) wycięty z pełnego PDF okładki KDP."""
    im = page_img(cover_pdf, 1, dpi)
    x1 = im.width - round(bleed * dpi)
    return im.crop((x1 - round(trim_w * dpi), round(bleed * dpi), x1, round((bleed + trim_h) * dpi)))


def shadow_paste(base, img, xy, blur=24, offset=(12, 18), opacity=130, rgb=(8, 10, 12)):
    x, y = xy
    pad = blur * 3
    alpha = img.split()[-1] if img.mode == "RGBA" else None
    sh = Image.new("L", (img.width + 2 * pad, img.height + 2 * pad), 0)
    if alpha is not None:
        sh.paste(alpha.point(lambda v: opacity if v > 0 else 0), (pad, pad))
    else:
        ImageDraw.Draw(sh).rectangle((pad, pad, pad + img.width, pad + img.height), fill=opacity)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.paste(Image.new("RGB", sh.size, rgb), (x - pad + offset[0], y - pad + offset[1]), sh)
    if alpha is not None:
        base.paste(img, (x, y), img)
    else:
        base.paste(img, (x, y))


def book_mockup(cover, height):
    """Okładka z krawędzią stron po prawej i miękkim cieniem przy grzbiecie."""
    w = round(cover.width * height / cover.height)
    cv = cover.resize((w, height), Image.LANCZOS)
    edge = max(6, w // 60)
    out = Image.new("RGBA", (w + edge, height), (0, 0, 0, 0))
    pages = Image.new("RGB", (edge, height - 8), "#efebe4")
    d = ImageDraw.Draw(pages)
    for i in range(0, edge, 2):
        d.line((i, 0, i, height), fill="#dcd6cc")
    out.paste(pages, (w, 4))
    out.paste(cv, (0, 0))
    ov = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    g = int(w * 0.05)
    for i in range(g):
        od.line((i, 0, i, height), fill=(0, 0, 0, int(70 * (1 - i / g))))
    for i in range(int(w * 0.25)):
        a = int(24 * (1 - abs(i - w * 0.125) / (w * 0.125)))
        od.line((int(w * 0.09) + i, 0, int(w * 0.09) + i, height), fill=(255, 255, 255, max(0, a)))
    out.alpha_composite(ov, (0, 0))
    return out


def spread(left, right, height):
    w = round(left.width * height / left.height)
    s = Image.new("RGB", (w * 2, height), "white")
    s.paste(left.resize((w, height), Image.LANCZOS), (0, 0))
    s.paste(right.resize((w, height), Image.LANCZOS), (w, 0))
    ov = Image.new("RGBA", s.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    g = int(w * 0.09)
    for i in range(g):
        a = int(80 * (1 - i / g) ** 2)
        od.line((w - i, 0, w - i, height), fill=(30, 30, 30, a))
        od.line((w + i, 0, w + i, height), fill=(30, 30, 30, a))
    return Image.alpha_composite(s.convert("RGBA"), ov).convert("RGB")


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


def text_lines(d, x, y, lines, fnt, fill, lead):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lead
    return y


def bullets(d, x, y, items, fnt, fill, dot, width, lead, gap=14):
    r = fnt.size * 0.2
    for it in items:
        lines = wrap(d, it, fnt, width - fnt.size)
        d.ellipse((x, y + fnt.size * 0.45 - r, x + 2 * r, y + fnt.size * 0.45 + r), fill=dot)
        y = text_lines(d, x + fnt.size * 0.9, y, lines, fnt, fill, lead) + gap
    return y


def caption_square(bg, page, crop_frac, title, sub, band, band_ink, band_sub, accent, size=1200):
    """Kwadrat A+: fragment strony na tle + pas z podpisem (dolne ~34%)."""
    im = bg.copy()
    band_h = round(size * 0.34)
    x0, y0, x1, y1 = crop_frac
    pg = page.crop((round(x0 * page.width), round(y0 * page.height), round(x1 * page.width), round(y1 * page.height)))
    pw = 980
    pg = pg.resize((pw, round(pg.height * pw / pg.width)), Image.LANCZOS)
    avail = size - band_h - 70
    if pg.height > avail:
        pg = pg.crop((0, 0, pg.width, avail))
    shadow_paste(im, pg, ((size - pw) // 2, 60))
    d = ImageDraw.Draw(im)
    d.rectangle((0, size - band_h, size, size), fill=band)
    d.rectangle((0, size - band_h, size, size - band_h + 10), fill=accent)
    d.text((60, size - band_h + 50), title, font=font("ExtraBold", 66), fill=band_ink)
    text_lines(d, 60, size - band_h + 140, wrap(d, sub, font("Regular", 36), size - 120), font("Regular", 36), band_sub, 48)
    return im
