#!/usr/bin/env python3
"""Render Golden Stitch art to PNG with headless Chromium (Playwright) and local p5.js.

    from render import render_png
    render_png({"seed": 7, "W": 2550, "H": 3300, ...}, "out.png")

or from the shell:  python render.py cfg.json out.png
"""
import base64
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="{p5}"></script><script src="{gs}"></script></head>
<body style="margin:0;background:#000">
<script>
window.CFG = {cfg};
new p5(function (p) {{
  p.setup = function () {{
    p.pixelDensity(1);
    p.createCanvas(CFG.W, CFG.H);
    p.noLoop();
    GoldenStitch.render(p, CFG);
    window.PNG = p.canvas.toDataURL('image/png');
  }};
}});
</script></body></html>"""


def render_many(jobs):
    """jobs: list of (cfg, out_path). One browser for all."""
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        for cfg, out in jobs:
            html = PAGE.format(p5=(HERE / "p5.min.js").as_uri(), gs=(HERE / "golden_stitch.js").as_uri(),
                               cfg=json.dumps(cfg))
            tmp = Path(out).resolve().with_suffix(".render.html")
            tmp.write_text(html, encoding="utf-8")
            pg.goto(tmp.as_uri())
            pg.wait_for_function("window.PNG !== undefined", timeout=600_000)
            data = pg.evaluate("window.PNG")
            Path(out).write_bytes(base64.b64decode(data.split(",", 1)[1]))
            tmp.unlink()
        br.close()


def render_png(cfg, out):
    render_many([(cfg, out)])


if __name__ == "__main__":
    render_png(json.loads(Path(sys.argv[1]).read_text()), sys.argv[2])
