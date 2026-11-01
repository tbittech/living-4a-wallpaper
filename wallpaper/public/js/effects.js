// Efectos por código del escenario (port de los _draw_* de Assets BBad/tools/effects.py).
// Lo que precalcula Python (_prep_*: formas, máscaras, tinta del pizarrón, luces, cajas) viene en el bundle.
// El azar es el mismo que en Python (crc32 del repr de la clave), así el resultado coincide con las referencias.
//
// Se dibuja en dos lienzos del tamaño de la escena: "under" (debajo de capas y personajes; también se pinta
// sobre los muebles recortados) y "over" (vapor, reflejos), igual que Effects.under / Effects.over.

// --- azar fijo por clave, idéntico a effects.rnd ---
const CRC = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});

function crc32(str) {
  let c = 0xffffffff;
  for (let i = 0; i < str.length; i++) c = CRC[(c ^ str.charCodeAt(i)) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

/** repr() de Python para strings, enteros y tuplas (lo que usan las claves). */
function pyrepr(v) {
  if (Array.isArray(v)) return `(${v.map(pyrepr).join(", ")}${v.length === 1 ? "," : ""})`;
  if (typeof v === "string") return `'${v}'`;
  return String(v);
}

export const rnd = (...k) => (crc32(pyrepr(k)) & 0xffffff) / 0x1000000;

function pyround(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 ? r - 1 : r;
}

/** Índice del tramo de tiempo en el que cae t (tramos de largo al azar entre lo y hi). */
export function steps(t, seed, lo, hi) {
  const b = Math.floor(t / hi);
  const cuts = 1 + Math.floor(rnd(seed, "cuts", b) * Math.max(1, pyround(hi / lo)));
  return b * 1000 + Math.floor((t - b * hi) / (hi / cuts));
}

const list = (v) => (v == null ? [] : typeof v === "string" ? [v] : v);
const rgb = (c, k = 1) => `rgb(${Math.trunc(c[0] * k)},${Math.trunc(c[1] * k)},${Math.trunc(c[2] * k)})`;

function image(src) {
  return new Promise((ok, fail) => {
    const img = new Image();
    img.onload = () => ok(img);
    img.onerror = () => fail(new Error(`No se pudo cargar ${src}`));
    img.src = src;
  });
}

function canvas(w, h) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return c;
}

export class Effects {
  static async load(bundle, base) {
    const fx = new Effects(bundle);
    const jobs = [];
    for (const d of Object.values(fx.data)) {
      for (const it of Object.values(d)) {
        if (it.img) jobs.push(image(base + it.img).then((img) => (it.image = img)));
      }
    }
    await Promise.all(jobs);
    return fx;
  }

  constructor(bundle) {
    const e = bundle.effects;
    this.px = e.px;
    this.config = e.config;
    this.data = e.data;
    [this.W, this.H] = bundle.size;
    this.under = canvas(this.W, this.H);
    this.over = canvas(this.W, this.H);
    this.tinted = new Map();   // formas coloreadas (glow / spill) por color
    this.boards = new Map();   // lienzo del pizarrón por fondo
  }

  /** None si el efecto no corre; si corre, desde cuándo. state: {lugar: {role, since}}. */
  active(e, state) {
    const roles = list(e.role), places = list(e.place);
    if (!roles.length && !places.length) return 0;
    let t0 = null;
    for (const [place, { role, since }] of Object.entries(state)) {
      if ((!roles.length || roles.includes(role)) && (!places.length || places.includes(place))) {
        t0 = t0 === null ? since : Math.min(t0, since);
      }
    }
    return t0;
  }

  /** Dibuja los dos lienzos para el fondo bg en el tiempo t. Devuelve qué lienzos tienen algo. */
  render(bg, t, state) {
    const used = { under: false, over: false };
    const ctxs = { under: this.under.getContext("2d"), over: this.over.getContext("2d") };
    for (const c of Object.values(ctxs)) {
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.globalAlpha = 1;
      c.clearRect(0, 0, this.W, this.H);
    }
    const data = this.data[bg] || {};
    for (const [name, e] of Object.entries(this.config)) {
      if (!(name in data)) continue;   // no va en este fondo
      const stage = e.stage ?? (e.type === "steam" ? "over" : "under");
      const t0 = this.active(e, state);
      if (t0 === null) continue;
      const ctx = ctxs[stage];
      ctx.globalAlpha = 1;
      this[`draw_${e.type}`](ctx, name, e, data[name], t, t - t0, bg);
      used[stage] = true;
    }
    return used;
  }

  // --- utilidades ---

  block(ctx, x, y, color, alpha = 1, size = null) {
    const s = size || this.px;
    x = Math.floor(Math.trunc(x) / s) * s;
    y = Math.floor(Math.trunc(y) / s) * s;
    if (x < 0 || y < 0 || x + s > this.W || y + s > this.H) return;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = rgb(color);
    ctx.fillRect(x, y, s, s);
    ctx.globalAlpha = 1;
  }

  boxFill(ctx, [x0, y0, x1, y1], color, alpha) {
    ctx.globalAlpha = alpha;
    ctx.fillStyle = rgb(color);
    ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.globalAlpha = 1;
  }

  /** Forma precalculada (alfa) pintada de un color, con alfa extra. */
  shape(ctx, d, color, alpha) {
    const k = `${d.img}|${color}`;
    let c = this.tinted.get(k);
    if (!c) {
      c = canvas(d.image.width, d.image.height);
      const g = c.getContext("2d");
      g.drawImage(d.image, 0, 0);
      g.globalCompositeOperation = "source-in";
      g.fillStyle = rgb(color);
      g.fillRect(0, 0, c.width, c.height);
      this.tinted.set(k, c);
    }
    ctx.globalAlpha = Math.min(1, alpha);
    ctx.drawImage(c, d.box[0], d.box[1]);
    ctx.globalAlpha = 1;
  }

  // --- glow: la tele ---
  draw_glow(ctx, name, e, d, t) {
    const [lo, hi] = e.flicker ?? [0.1, 0.4];
    const i = steps(t, name, lo, hi);
    const levels = e.alpha ?? [0.1, 0.2, 0.3];
    const level = levels[Math.floor(rnd(name, "lvl", i) * levels.length)];
    const colors = e.colors ?? [[200, 220, 255]];
    const scene = Math.floor(t / (e.scene_s ?? 1.6));
    const color = colors[Math.floor(rnd(name, "col", scene) * colors.length)];
    this.shape(ctx, d, color, level * 2);
    if (e.rim) this.boxFill(ctx, e.rim, color, Math.min(1, level * 2.5));
  }

  // --- board: el pizarrón (se borra la tinta y se vuelve a escribir) ---
  draw_board(ctx, name, e, d, t, since, bg) {
    const n = d.xs.length;
    const write = e.write_s ?? 8, hold = e.hold_s ?? 2, erase = e.erase_s ?? 0.8;
    const f = since % (write + hold + erase);
    let b = this.boards.get(bg);
    if (!b) {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (let i = 0; i < n; i++) {
        x0 = Math.min(x0, d.xs[i]); x1 = Math.max(x1, d.xs[i]);
        y0 = Math.min(y0, d.ys[i]); y1 = Math.max(y1, d.ys[i]);
      }
      const c = canvas(x1 - x0 + 1, y1 - y0 + 1);
      b = { c, x0, y0, x1, key: null };
      this.boards.set(bg, b);
    }
    // Qué píxeles de tinta van tapados de blanco (y dónde está la punta del marcador)
    let from = 0, to = 0, cut = null, tip = -1;
    if (f < write) {
      from = Math.floor((n * Math.floor((f / write) * 40)) / 40);
      to = n;
      if (from > 0 && from < n) tip = from - 1;
    } else if (f >= write + hold) {
      const k = (f - write - hold) / erase;
      cut = b.x0 + (b.x1 - b.x0 + 1) * k;
    }
    const key = `${from}|${to}|${cut}`;
    if (key !== b.key) {
      b.key = key;
      const g = b.c.getContext("2d");
      const img = g.createImageData(b.c.width, b.c.height);
      const w = Math.trunc(d.white[0]), wg = Math.trunc(d.white[1]), wb = Math.trunc(d.white[2]);
      const paint = (i, r, gg, bb) => {
        const o = ((d.ys[i] - b.y0) * b.c.width + (d.xs[i] - b.x0)) * 4;
        img.data[o] = r; img.data[o + 1] = gg; img.data[o + 2] = bb; img.data[o + 3] = 255;
      };
      if (cut !== null) {
        for (let i = 0; i < n; i++) if (d.xs[i] < cut) paint(i, w, wg, wb);
      } else {
        for (let i = from; i < to; i++) paint(i, w, wg, wb);
        if (tip >= 0) paint(tip, ...(e.marker ?? [40, 60, 160]));
      }
      g.putImageData(img, 0, 0);
    }
    ctx.drawImage(b.c, b.x0, b.y0);
  }

  // --- clouds: nubes de día, solo sobre el cielo ---
  draw_clouds(ctx, name, e, d, t) {
    const s = d.s;
    const colors = e.colors ?? [[255, 255, 255], [220, 234, 240]];
    const [bx0, by0, bx1, by1] = d.box;
    if (!d.layer) d.layer = canvas(bx1 - bx0, by1 - by0);
    const g = d.layer.getContext("2d");
    g.globalCompositeOperation = "source-over";
    g.clearRect(0, 0, d.layer.width, d.layer.height);
    for (const cl of d.clouds) {
      const [lo, hi] = cl.span;
      let x = lo + ((cl.x * (hi - lo) + t * cl.speed) % (hi - lo));
      x = Math.floor(Math.trunc(x) / s) * s;
      for (const [xx, yy, bottom] of cl.cells) {
        const X = x + xx * s - bx0, Y = cl.y + yy * s - by0;
        if (X >= 0 && X + s <= bx1 - bx0 && Y >= 0 && Y + s <= by1 - by0) {
          g.fillStyle = rgb(bottom ? colors[1] : colors[0]);
          g.fillRect(X, Y, s, s);
        }
      }
    }
    g.globalCompositeOperation = "destination-in";
    g.drawImage(d.image, 0, 0);
    g.globalCompositeOperation = "source-over";
    ctx.globalAlpha = e.alpha ?? 0.9;
    ctx.drawImage(d.layer, bx0, by0);
    ctx.globalAlpha = 1;
  }

  // --- lights: luces de la ciudad que titilan y ventanitas extra ---
  draw_lights(ctx, name, e, d, t) {
    const [lo, hi] = e.period ?? [0.5, 3.0];
    const off = e.off_chance ?? 0.25;
    d.comps.forEach((comp, k) => {
      const i = steps(t, [name, k], lo, hi);
      if (rnd(name, k, i, "off") < off) {
        ctx.globalAlpha = e.dim ?? 0.75;
        ctx.fillStyle = rgb(comp.dark);
        for (let j = 0; j < comp.px.length; j += 2) ctx.fillRect(comp.px[j], comp.px[j + 1], 1, 1);
        ctx.globalAlpha = 1;
      }
    });
    const colors = e.colors ?? [[255, 214, 120]];
    d.extra.forEach(([x, y], k) => {
      const i = steps(t, [name, "x", k], lo * 2, hi * 2);
      if (rnd(name, "x", k, i, "on") < (e.on_chance ?? 0.55)) {
        this.block(ctx, x, y, colors[Math.floor(rnd(name, "xc", k) * colors.length)]);
      }
    });
  }

  // --- sprite: cajas de comida china (bloques ya con la luz del fondo) ---
  draw_sprite(ctx, name, e, d) {
    for (const [x, y, s, r, g, b] of d.blocks) this.block(ctx, x, y, [r, g, b], 1, s);
  }

  // --- steam: vapor que sube en bloques ---
  draw_steam(ctx, name, e, d, t) {
    const n = e.particles ?? 5;
    const height = e.height ?? 24, rate = e.rate ?? 0.5;
    const colors = e.colors ?? [[240, 240, 240], [210, 214, 220]];
    const alphas = e.alpha ?? [0.6, 0.4, 0.2];
    d.sources.forEach(([x0, y0], si) => {
      for (let k = 0; k < n; k++) {
        const f = (((t * rate * (0.8 + 0.4 * rnd(name, si)) + k / n + rnd(name, si, k)) % 1) + 1) % 1;
        const y = y0 - 2 - f * height;
        const x = x0 + (e.sway ?? 3) * Math.sin(2 * Math.PI * (f * 1.2 + rnd(name, si, k, "p")));
        const band = Math.min(alphas.length - 1, Math.floor(f * alphas.length));
        const col = band === 0 ? colors[0] : colors[colors.length - 1];
        this.block(ctx, x, y, col, alphas[band]);
        if (f < 0.5) this.block(ctx, x + this.px, y, col, alphas[band] * 0.7);
      }
    });
  }

  // --- screen: pantallas de las compus ---
  draw_screen(ctx, name, e, d, t) {
    const colors = e.colors ?? [[90, 230, 140], [150, 210, 255], [230, 240, 255]];
    const bright = e.flicker_alpha ?? [0.92, 1.0, 0.96];
    const lvl = bright[steps(t, name, 0.08, 0.3) % bright.length];
    if (e.rect) {
      const [x0, y0, x1, y1] = e.rect;
      this.boxFill(ctx, e.rect, e.bg_color ?? [18, 28, 52], 1);
      const lineH = e.line_h ?? 3;
      const scroll = Math.floor(t * (e.lines_per_s ?? 4));
      const rows = Math.floor((y1 - y0) / lineH);
      for (let r = 0; r < rows; r++) {
        const k = scroll + r;
        const length = Math.floor((x1 - x0 - 3) * (0.25 + 0.7 * rnd(name, k, "len")));
        const indent = 2 * Math.floor(rnd(name, k, "ind") * 3);
        if (rnd(name, k, "blank") < 0.15) continue;
        const col = colors[Math.floor(rnd(name, k, "c") * colors.length)];
        const xs = x0 + 1 + indent;
        const xe = Math.min(x1 - 1, xs + length);
        if (xe > xs) {
          ctx.fillStyle = rgb(col, lvl);
          ctx.fillRect(xs, y0 + 1 + r * lineH, xe - xs, 1);
        }
      }
      if (Math.floor(t * 2) % 2 === 0) {
        ctx.fillStyle = rgb(colors[colors.length - 1]);
        ctx.fillRect(x0 + 2, y0 + 1 + (rows - 1) * lineH, 2, 2);
      }
    }
    if (e.rim) this.boxFill(ctx, e.rim, e.light ?? [170, 210, 255], 0.8 * lvl);
  }

  // --- spill: reflejo de la pantalla sobre quien la mira ---
  draw_spill(ctx, name, e, d, t) {
    const lvl = (e.flicker_alpha ?? [0.8, 1.0, 0.9])[steps(t, name, 0.08, 0.3) % 3];
    this.shape(ctx, d, e.light ?? [170, 210, 255], (e.alpha ?? 0.3) * lvl);
  }
}
