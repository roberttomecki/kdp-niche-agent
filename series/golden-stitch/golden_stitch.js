/* Golden Stitch – generative cover art for a book series (p5.js, instance-mode friendly).
 *
 * Vogel phyllotaxis: unit n at angle n·GA (golden angle) and radius c·√n.
 * Colour by arithmetic: spiral arm = n mod F (Fibonacci), shifted at Fibonacci-sized rounds.
 * Each unit is rendered as a crochet chain loop of plied yarn, aligned with its spiral arm.
 *
 * Usage:  GoldenStitch.render(p, cfg)   – p is a p5 instance (or the global p5 in global mode)
 * All lengths in cfg are in pixels. Same seed → same image.
 */
(function (root) {
  const GA = Math.PI * (3 - Math.sqrt(5));          // 137.507764…° in radians
  const FIB = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181];

  function mix(p, a, b, t) { return p.lerpColor(p.color(a), p.color(b), t); }

  function grain(p, cfg) {
    const n = Math.floor(cfg.W * cfg.H / 900 * cfg.grain);
    p.noStroke();
    for (let i = 0; i < n; i++) {
      const light = p.random() < 0.5;
      p.fill(light ? 255 : 0, light ? 7 : 9);
      const s = p.random(0.6, 1.8) * cfg.unitPx / 90;
      p.rect(p.random(cfg.W), p.random(cfg.H), s, s);
    }
  }

  // one chain loop of plied yarn, centred at origin, long axis along +x
  function yarnLoop(p, L, Wd, sw, col, cfg) {
    const shadow = mix(p, col, cfg.ground, 0.55);
    const deep = mix(p, col, '#000000', 0.38);
    const hi = mix(p, col, '#ffffff', 0.45);
    p.noFill();
    // cast shadow on the ground
    p.stroke(p.red(cfg.shade), p.green(cfg.shade), p.blue(cfg.shade), 120);
    p.strokeWeight(sw * 1.25);
    p.ellipse(sw * 0.16, sw * 0.22, L, Wd);
    // body
    p.stroke(shadow); p.strokeWeight(sw * 1.08); p.ellipse(0, 0, L, Wd);
    p.stroke(col); p.strokeWeight(sw * 0.82); p.ellipse(-sw * 0.05, -sw * 0.06, L, Wd);
    // highlight on the lit side (light from upper left)
    p.stroke(hi); p.strokeWeight(sw * 0.26);
    p.arc(-sw * 0.12, -sw * 0.14, L, Wd, Math.PI * 1.02, Math.PI * 1.62);
    p.arc(-sw * 0.12, -sw * 0.14, L, Wd, Math.PI * 0.02, Math.PI * 0.18);
    // ply twist: short diagonal ticks across the strand
    p.stroke(p.red(deep), p.green(deep), p.blue(deep), 150);
    p.strokeWeight(Math.max(0.6, sw * 0.12));
    const ticks = cfg.plyTicks;
    for (let k = 0; k < ticks; k++) {
      const t = (k + 0.5) / ticks * Math.PI * 2;
      const x = (L / 2) * Math.cos(t), y = (Wd / 2) * Math.sin(t);
      let tx = -(L / 2) * Math.sin(t), ty = (Wd / 2) * Math.cos(t);
      const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
      const nx = -ty, ny = tx, a = sw * 0.36, b = sw * 0.22;
      p.line(x - nx * a + tx * b, y - ny * a + ty * b, x + nx * a - tx * b, y + ny * a - ty * b);
    }
  }

  function yarnPath(p, pts, sw, col, cfg) {
    const draw = (dx, dy) => { p.beginShape(); for (const q of pts) p.curveVertex(q[0] + dx, q[1] + dy); p.endShape(); };
    p.noFill();
    p.stroke(p.red(cfg.shade), p.green(cfg.shade), p.blue(cfg.shade), 120); p.strokeWeight(sw * 1.2); draw(sw * 0.16, sw * 0.22);
    p.stroke(mix(p, col, cfg.ground, 0.55)); p.strokeWeight(sw * 1.05); draw(0, 0);
    p.stroke(col); p.strokeWeight(sw * 0.8); draw(-sw * 0.05, -sw * 0.06);
    p.stroke(mix(p, col, '#ffffff', 0.45)); p.strokeWeight(sw * 0.22); draw(-sw * 0.18, -sw * 0.2);
    const deep = mix(p, col, '#000000', 0.38);
    p.stroke(p.red(deep), p.green(deep), p.blue(deep), 150); p.strokeWeight(Math.max(0.6, sw * 0.12));
    for (let i = 1; i < pts.length - 2; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const segs = Math.max(1, Math.round(Math.hypot(x1 - x0, y1 - y0) / (sw * 0.9)));
      for (let s = 0; s < segs; s++) {
        const t = s / segs, x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t;
        let tx = x1 - x0, ty = y1 - y0; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
        const nx = -ty, ny = tx, a = sw * 0.36, b = sw * 0.22;
        p.line(x - nx * a + tx * b, y - ny * a + ty * b, x + nx * a - tx * b, y + ny * a - ty * b);
      }
    }
  }

  function render(p, cfg) {
    cfg = Object.assign({
      seed: 1, W: 1200, H: 1200, cx: 742, cy: 458, count: 1300, spacing: 14,
      armsF: 21, roundsF: true, jitter: 0.18, loopScale: 1.0, grain: 1.0, plyTicks: 9,
      tail: true, tailAngle: -2.4, unitPx: 90,
      ground: '#2a1730', shade: '#12070f', yarns: ['#f2a03d', '#e2574c', '#f6e7cf', '#3fa39a'],
    }, cfg);
    cfg.shade = p.color(cfg.shade);
    p.randomSeed(cfg.seed); p.noiseSeed(cfg.seed);
    p.background(cfg.ground);
    if (cfg.grain > 0) grain(p, cfg);

    const c = cfg.spacing, pts = [];
    for (let n = 1; n <= cfg.count; n++) {
      const nz = p.noise(n * 0.031, 7.3) - 0.5, nr = p.noise(n * 0.027, 19.1) - 0.5;
      const a = n * GA + nz * cfg.jitter * 0.12;
      const r = c * Math.sqrt(n) * (1 + nr * cfg.jitter * 0.08);
      pts.push([cfg.cx + r * Math.cos(a), cfg.cy + r * Math.sin(a), a, r]);
    }
    // round index: how many Fibonacci thresholds the unit has passed
    const zone = (n) => { let z = 0; for (const f of FIB) if (n > f && f >= 55) z++; return z; };
    const k = cfg.yarns.length;
    const d = c * Math.sqrt(Math.PI);                  // mean spacing between neighbours

    for (let i = pts.length - 1; i >= 0; i--) {
      const n = i + 1, [x, y] = pts[i];
      if (x < -d * 2 || y < -d * 2 || x > cfg.W + d * 2 || y > cfg.H + d * 2) continue;
      // orientation: toward the neighbour on the same arm (n − F)
      const j = i - cfg.armsF;
      let ang;
      if (j >= 0) ang = Math.atan2(y - pts[j][1], x - pts[j][0]);
      else ang = pts[i][2] + Math.PI / 2;
      ang += (p.noise(n * 0.05, 3.7) - 0.5) * cfg.jitter * 0.9;
      const arm = n % cfg.armsF;
      const ci = (arm + (cfg.roundsF ? zone(n) : 0)) % k;
      const L = d * 1.18 * cfg.loopScale * (1 + (p.noise(n * 0.09, 11) - 0.5) * cfg.jitter * 0.5);
      const Wd = L * 0.6, sw = L * 0.21;
      p.push(); p.translate(x, y); p.rotate(ang);
      yarnLoop(p, L, Wd, sw, cfg.yarns[ci], cfg);
      p.pop();
    }

    if (cfg.tail) {
      // the one free strand: leaves the outermost visible round and drifts away
      let best = pts.length - 1;
      for (let i = pts.length - 1; i > pts.length - 60; i--) {
        const a = Math.atan2(pts[i][1] - cfg.cy, pts[i][0] - cfg.cx);
        const da = Math.abs(Math.atan2(Math.sin(a - cfg.tailAngle), Math.cos(a - cfg.tailAngle)));
        const db = Math.abs(Math.atan2(Math.sin(Math.atan2(pts[best][1] - cfg.cy, pts[best][0] - cfg.cx) - cfg.tailAngle), Math.cos(Math.atan2(pts[best][1] - cfg.cy, pts[best][0] - cfg.cx) - cfg.tailAngle)));
        if (da < db) best = i;
      }
      let [x, y] = pts[best], heading = cfg.tailAngle;
      const path = [[x, y], [x, y]], step = d * 0.9;
      for (let s = 0; s < 220; s++) {
        heading += (p.noise(s * 0.045, 41) - 0.5) * 0.22;
        x += Math.cos(heading) * step; y += Math.sin(heading) * step;
        path.push([x, y]);
        if (x < -step * 3 || y < -step * 3 || x > cfg.W + step * 3 || y > cfg.H + step * 3) break;
      }
      path.push([x, y]);
      yarnPath(p, path, d * 1.18 * 0.21, cfg.yarns[0], cfg);
    }
  }

  root.GoldenStitch = { render, GA, FIB };
})(typeof window !== 'undefined' ? window : globalThis);
