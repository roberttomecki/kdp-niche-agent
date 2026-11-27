#!/usr/bin/env python3
"""Kontrola PDF wnętrza KDP: elementy poza marginesami i nieosadzone fonty.

python check_pdf.py plik.pdf --gutter 0.625 --outer 0.5 --top 0.5 --bottom 0.5
Strony nieparzyste mają grzbiet po lewej. Tolerancja 0,5 pt.
"""
import argparse
import sys

import pdfplumber
from pypdf import PdfReader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--gutter", type=float, required=True)
    ap.add_argument("--outer", type=float, required=True)
    ap.add_argument("--top", type=float, required=True)
    ap.add_argument("--bottom", type=float, required=True)
    a = ap.parse_args()
    bad = 0
    with pdfplumber.open(a.pdf) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            W, H = page.width, page.height
            left = (a.gutter if i % 2 else a.outer) * 72 - 0.5
            right = W - (a.outer if i % 2 else a.gutter) * 72 + 0.5
            top, bottom = a.top * 72 - 0.5, H - a.bottom * 72 + 0.5   # pdfplumber: y od góry
            objs = page.chars + page.lines + page.rects + page.curves + page.images
            for o in objs:
                if o["x0"] < left or o["x1"] > right or o["top"] < top or o["bottom"] > bottom:
                    bad += 1
                    if bad <= 15:
                        print(f"str. {i}: {o.get('object_type')} {o.get('text', '')!r} "
                              f"x0={o['x0']:.1f} x1={o['x1']:.1f} top={o['top']:.1f} bottom={o['bottom']:.1f}")
        n = len(pdf.pages)
    fonts = set()
    for p in PdfReader(a.pdf).pages:
        res = p.get("/Resources") or {}
        for f in (res.get("/Font") or {}).values():
            f = f.get_object()
            desc = f.get("/FontDescriptor")
            if desc is None and "/DescendantFonts" in f:
                desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            emb = bool(desc) and any(k in desc.get_object() for k in ("/FontFile", "/FontFile2", "/FontFile3"))
            fonts.add((str(f.get("/BaseFont")), emb))
    print(f"stron: {n}, elementów poza marginesami: {bad}")
    for name, emb in sorted(fonts):
        print(f"  font {name}: {'osadzony' if emb else 'NIEOSADZONY'}")
    if bad or any(not e for _, e in fonts):
        sys.exit(1)


if __name__ == "__main__":
    main()
