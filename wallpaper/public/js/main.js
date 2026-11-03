// Wallpaper: el living del tema en vivo. Arranque, bucle a ~30 FPS y dibujo de la escena.
//
// Parámetros de la URL: ?demo=1 (simulador de eventos; ?demo=manual solo con teclas), ?debug=1 (casillas,
// lugares y estado), ?bg=day|night_idle|night_active (fondo fijo), ?fit=contain, ?leave=30 (segundos sin
// eventos para irse), ?sources=claude,codex,gemini (IAs del simulador; por defecto solo claude),
// ?ref=NOMBRE (dibuja una escena de referencia de export_bundle.py y la compara con la de Python; &diff=1 muestra
// las diferencias), ?server=127.0.0.1:8775 (servidor de eventos en otro lado; por defecto el mismo que sirve la página).
// Sin ?demo ni ?ref se conecta al servidor (net.js); con ?debug=1 las teclas del simulador también andan ahí.

import { loadBundle } from "./bundle.js";
import { Grid } from "./grid.js";
import { compose } from "./layers.js";
import { Scaler } from "./scaler.js";
import { Effects } from "./effects.js";
import { Demo, bindKeys } from "./demo.js";
import { connect, eventFor } from "./net.js";
import { Character, spriteActor } from "./sim/character.js";
import { chatter } from "./sim/chatter.js";
import { wander } from "./sim/scenes.js";
import { World } from "./sim/world.js";

const params = new URLSearchParams(location.search);
const config = await (await fetch("config.json")).json();
if (params.has("leave")) config.leave_after = Number(params.get("leave"));
let debug = params.get("debug") === "1";

const theme = params.get("theme") || config.theme;
// Lo propio de cada tema (home, disputas, disfraces, escenas, charla) pisa lo general: config.themes.<tema>
Object.assign(config, config.themes?.[theme] || {});
const b = await loadBundle(theme);
const fx = await Effects.load(b, `bundle/${theme}/`);
const grid = new Grid(b);
const world = new World(b, grid, config);
const bySource = {};
for (const [source, id] of Object.entries(b.cast)) {
  if (!b.characters[id]) continue;
  const ch = new Character(world, source, id, b.characters[id]);
  world.add(ch);
  bySource[source] = ch;
}

/** Entrada única de eventos: simulador, teclas o WebSocket (net.js). */
function onEvent(ev) {
  bySource[ev.source]?.handle(ev);
  log.unshift(`${ev.source} ${ev.type}${ev.tool ? ` ${ev.tool}` : ""}`);
  log.length = Math.min(log.length, 6);
}
const log = [];

/**
 * Estado del servidor al conectar. En la primera carga los presentes aparecen directo en su lugar;
 * en una reconexión solo se corrige quién está y qué hace (pudo perderse algún evento).
 */
function onSnapshot(snap, first) {
  for (const [source, ch] of Object.entries(bySource)) {
    const a = snap.agents?.[source];
    if (!a?.present) {
      if (!first && ch.present) onEvent({ source, type: "session_end" });   // cerró mientras no había conexión
      continue;
    }
    // Sesión abierta pero sin eventos hace rato: está en su pieza y vuelve por ahí con el próximo evento
    const age = Math.max(0, (snap.server_ts - a.last_ts) / 1000);
    if (!ch.present && config.leave_after > 0 && age > config.leave_after * (a.role === "rest" ? 1 : 4)) {
      if (first) ch.exit = ch.home;
      continue;
    }
    if (!ch.present || ch.role !== a.role || ch.effort !== (a.effort ?? ch.effort)) onEvent(eventFor(source, a));
    if (first) ch.placeNow();
    ch.lastEvent = world.now - age;
  }
}

let demo = null, net = null, help = "", selected = "claude";
if (params.has("demo") || (debug && !params.has("ref"))) {
  // ?demo: simulador; solo con ?debug=1 (conectado al servidor): las teclas, sin eventos automáticos
  const sources = params.has("demo") ? (params.get("sources") || "claude").split(",").filter((s) => bySource[s])
                                     : Object.keys(bySource);
  if (params.has("demo") && !params.has("leave")) config.leave_after = config.demo_leave_after ?? 180;
  demo = new Demo(onEvent, sources, config.leave_after);
  demo.auto = params.has("demo") && params.get("demo") !== "manual";
  const sel = () => bySource[selected];
  help = bindKeys(demo, () => selected, (s) => (selected = s), sources, {
    d: () => (debug = !debug),
    // Escenas especiales: las hace quien tenga ese disfraz (Sheldon Flash, Leonard Frodo)
    f: () => world.chars.find((c) => config.costumes?.[c.id]?.flash)?.startSpecial("flash"),
    h: () => world.chars.find((c) => config.costumes?.[c.id]?.hobbit)?.startSpecial("hobbit"),
    w: () => sel()?.present && !sel().script && sel().startScript(wander(sel())),
    g: () => world.chars.find((c) => config.scenes.wii?.who.includes(c.id))?.startWii(),
    m: () => world.chars.find((c) => config.scenes.blanket?.who.includes(c.id))?.startBlanket(),
  });
}
if (!params.has("demo") && !params.has("ref")) {
  // Servida por server.py: su mismo host. Como archivo local (Lively la sirve en un host virtual *.localhost, o
  // file://): config.server. Sin servidor el living se ve igual, vacío, y net.js reintenta hasta que aparezca.
  const own = location.protocol === "http:" && !location.hostname.endsWith(".localhost");
  const host = params.get("server") || (own ? location.host : config.server);
  net = connect(`ws://${host}/ws`, { onSnapshot, onEvent });
}

// --- fondo: día por la hora; de noche, con agentes o sin agentes. Fundido entre fondos ---
let bgCur = null, bgPrev = null, bgT = 1;

function wantedBg() {
  if (params.has("bg")) return params.get("bg");
  const d = new Date();
  const h = d.getHours() + d.getMinutes() / 60;
  if (h >= config.day_hours[0] && h < config.day_hours[1]) return "day";
  return world.anyPresent ? "night_active" : "night_idle";
}

function updateBg(dt) {
  const want = wantedBg();
  if (bgCur === null) bgCur = want;
  else if (want !== bgCur) {
    bgPrev = bgCur;
    bgCur = want;
    bgT = 0;
  }
  bgT = Math.min(1, bgT + dt / config.crossfade);
}

function drawFaded(ctx, imgs, x, y) {
  if (bgT < 1 && bgPrev) {
    ctx.drawImage(imgs[bgPrev], x, y);
    ctx.globalAlpha = bgT;
  }
  ctx.drawImage(imgs[bgCur], x, y);
  ctx.globalAlpha = 1;
}

// --- dibujo ---
const [W, H] = b.size;
const scene = document.createElement("canvas");
scene.width = W;
scene.height = H;
const sctx = scene.getContext("2d");
sctx.imageSmoothingEnabled = false;
const screen = document.getElementById("screen");
const scaler = new Scaler(screen, W, H, params.get("fit") || "cover");
const tmp = document.createElement("canvas");

/** Estado de los efectos: {lugar: {role, since}} de quien está trabajando en un lugar. */
function effectState() {
  const out = {};
  for (const c of world.chars) {
    const s = c.effectState();
    if (s) out[s.place] = { role: s.role, since: s.since };
  }
  return out;
}

/** Escena nativa: fondo, efectos de abajo, personajes y muebles que los tapan, efectos de arriba. */
function drawScene(actors, t, state) {
  const k = bgT < 1 && bgPrev ? bgT : 1;   // los efectos del fondo nuevo aparecen con el fundido
  const used = fx.render(bgCur, t, state);
  drawFaded(sctx, b.bg, 0, 0);
  if (debug) drawGrid(sctx);
  if (used.under) {
    sctx.globalAlpha = k;
    sctx.drawImage(fx.under, 0, 0);
    sctx.globalAlpha = 1;
  }
  compose(sctx, b.layers, actors, (ctx, l) => {
    if (!used.under) return drawFaded(ctx, l.imgs, l.pos[0], l.pos[1]);
    // Los efectos de abajo también van sobre el mueble, solo donde hay mueble (como Effects.under)
    tmp.width = l.size[0];
    tmp.height = l.size[1];
    const g = tmp.getContext("2d");
    drawFaded(g, l.imgs, 0, 0);
    g.globalCompositeOperation = "source-atop";
    g.globalAlpha = k;
    g.drawImage(fx.under, -l.pos[0], -l.pos[1]);
    ctx.drawImage(tmp, l.pos[0], l.pos[1]);
  });
  if (used.over) {
    sctx.globalAlpha = k;
    sctx.drawImage(fx.over, 0, 0);
    sctx.globalAlpha = 1;
  }
}

// --- Frodo: mundo de las sombras, chispas y destello del Anillo (frodo_preview.tinted / sparks / glints) ---
const GOLD = ["rgb(255,236,140)", "rgb(255,205,70)", "rgb(214,150,40)"];
const shade = document.createElement("canvas");
shade.width = W;
shade.height = H;

function mulberry(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function drawSpecial(ctx, now) {
  const k = world.tint;
  if (k > 0) {
    // Gris y un poco más oscuro (TINT 0,7 y DARK 0,82 en frodo_preview.py)
    shade.getContext("2d").drawImage(scene, 0, 0);
    ctx.filter = `grayscale(${0.7 * k}) brightness(${1 - 0.18 * k})`;
    ctx.drawImage(shade, 0, 0);
    ctx.filter = "none";
  }
  world.fx = world.fx.filter((f) => now - f.t0 < 1);
  for (const f of world.fx) {
    const t = now - f.t0;
    if (f.kind === "sparks") {
      // Bloques de 2 px que salen del cuerpo, suben y se apagan titilando
      const rnd = mulberry(f.seed);
      const tick = Math.floor(now * 20);
      for (let i = 0; i < 16; i++) {
        const vx = -28 + 56 * rnd(), vy = -55 + 40 * rnd();
        const x0 = f.x - 10 + 20 * rnd(), y0 = f.y - 45 + 50 * rnd();
        const life = 0.45 + 0.55 * rnd();
        if (t > life || (t > life * 0.6 && (tick + i) % 2)) continue;
        const x = Math.floor((x0 + vx * t) / 2) * 2, y = Math.floor((y0 + vy * t + 20 * t * t) / 2) * 2;
        ctx.fillStyle = GOLD[Math.min(2, Math.floor((t / life) * 3))];
        ctx.fillRect(x, y, 2, 2);
      }
    } else if (f.kind === "glint") {
      // Cruz dorada que crece y se achica en 0,4 s
      const i = Math.floor(t * 20);
      if (i >= 8) continue;
      const r = [1, 2, 4, 6, 5, 3, 2, 1][i];
      for (let d = -r; d <= r; d++) {
        ctx.fillStyle = Math.abs(d) <= r >> 1 ? GOLD[0] : GOLD[1];
        ctx.fillRect(f.x + d, f.y, 1, 1);
        ctx.fillRect(f.x, f.y + d, 1, 1);
      }
      if (r >= 3) {
        ctx.fillStyle = GOLD[0];
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) ctx.fillRect(f.x + dx, f.y + dy, 1, 1);
      }
    }
  }
}

function render() {
  drawScene(world.chars.flatMap((c) => c.actors()), world.now, effectState());
  drawSpecial(sctx, world.now);
  scaler.present(scene);
  drawBubbles(screen.getContext("2d"));
  if (debug) drawHud(screen.getContext("2d"));
}

/** Globos de diálogo sobre la cabeza, dibujados en la pantalla (texto nítido) con borde de bloques. */
function drawBubbles(ctx) {
  const s = scaler.scale;
  const px = Math.max(2, Math.round(s));          // un píxel nativo en la pantalla
  for (const c of world.chars) {
    if (!c.say || !c.box) continue;
    const [x0, y0, x1] = c.box;
    const [sx, sy] = scaler.toScreen((x0 + x1) / 2, y0 - 4);
    ctx.save();
    ctx.font = `bold ${Math.round(9 * s)}px "Courier New", monospace`;
    ctx.textBaseline = "middle";
    const pad = 4 * px;
    const w = Math.ceil(ctx.measureText(c.say.text).width + 2 * pad);
    const h = Math.round(9 * s) + 2 * pad;
    const bx = Math.round(Math.min(Math.max(sx - w / 2, px), screen.width - w - px));
    const by = Math.round(sy - h - 3 * px);
    const tx = Math.round(Math.min(Math.max(sx, bx + 3 * px), bx + w - 6 * px));
    ctx.fillStyle = "#1c1a24";
    ctx.fillRect(bx - px, by - px, w + 2 * px, h + 2 * px);
    ctx.fillRect(tx - px, by + h, 4 * px, 2 * px);
    ctx.fillRect(tx, by + h + 2 * px, 2 * px, 2 * px);
    ctx.fillStyle = "#fbf7ec";
    ctx.fillRect(bx, by, w, h);
    ctx.fillRect(tx, by + h - px, 2 * px, 2 * px);
    ctx.fillStyle = "#1c1a24";
    ctx.fillText(c.say.text, bx + pad, by + h / 2 + px / 2);
    ctx.restore();
  }
}

function drawGrid(ctx) {
  ctx.save();
  ctx.lineWidth = 0.6;
  ctx.strokeStyle = "rgba(0, 255, 255, 0.45)";
  for (const [a, bb] of grid.tiles) {
    const p = grid.polygon(a, bb);
    ctx.beginPath();
    p.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.closePath();
    ctx.stroke();
  }
  ctx.fillStyle = "#f0f";
  for (const p of Object.values(b.places)) ctx.fillRect(p.foot[0] - 2, p.foot[1] - 2, 4, 4);
  ctx.restore();
}

let fps = 0;
function hudLines() {
  return [
    `${fps.toFixed(0)} fps · ${bgCur} · escala ${scaler.scale.toFixed(2)} (×${scaler.k}) · t ${world.now.toFixed(0)} s`,
    ...world.chars.filter((c) => c.present || c.source === selected).map((c) =>
      `${c.source === selected ? ">" : " "} ${c.id}${c.costume ? `[${c.costume}]` : ""}: ${c.state} rol=${c.role} ` +
      `lugar=${c.targetKey ?? "-"} casilla=${c.tile} ${c.anim}`),
    ...(net ? [`servidor: ${net.status}`] : []),
    ...(demo ? [`auto ${demo.auto ? "sí" : "no"} · ${help}`] : []),
    ...log.map((l) => `  ${l}`),
  ];
}

function drawHud(ctx, lines = hudLines(), labels = true) {
  const dpr = devicePixelRatio || 1;
  ctx.save();
  ctx.font = `${12 * dpr}px monospace`;
  ctx.textBaseline = "top";
  if (labels) {
    for (const [name, p] of Object.entries(b.places)) {
      const [x, y] = scaler.toScreen(p.foot[0], p.foot[1]);
      ctx.fillStyle = "#000";
      ctx.fillText(name, x + 5 * dpr + 1, y + 1);
      ctx.fillStyle = "#ff0";
      ctx.fillText(name, x + 5 * dpr, y);
    }
  }
  const lh = 15 * dpr;
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 0, Math.max(...lines.map((l) => ctx.measureText(l).width)) + 16 * dpr, lines.length * lh + 10 * dpr);
  ctx.fillStyle = "#fff";
  lines.forEach((l, i) => ctx.fillText(l, 8 * dpr, 5 * dpr + i * lh));
  ctx.restore();
}

// --- escena de referencia: misma escena que export_bundle.py compuso con Python ---
async function renderRef(name) {
  const ref = b.refs.find((r) => r.name === name);
  if (!ref) throw new Error(`No hay referencia '${name}'. Hay: ${b.refs.map((r) => r.name).join(", ")}`);
  bgCur = ref.bg;
  const actors = ref.actors.map(([id, place, anim]) => {
    const p = b.places[place];
    const c = b.characters[id];
    return spriteActor(c.img, c.anims[anim], 0, p.foot, p.tile, b.facings[p.facing].flip);
  });
  drawScene(actors, ref.t, ref.state);
  const img = new Image();
  img.src = `bundle/${theme}/${ref.img}`;
  await img.decode();
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const g = c.getContext("2d");
  g.drawImage(img, 0, 0);
  const py = g.getImageData(0, 0, W, H).data, js = sctx.getImageData(0, 0, W, H).data;
  let bad = 0, max = 0;
  const out = g.createImageData(W, H);
  for (let i = 0; i < py.length; i += 4) {
    const d = Math.max(Math.abs(py[i] - js[i]), Math.abs(py[i + 1] - js[i + 1]), Math.abs(py[i + 2] - js[i + 2]));
    max = Math.max(max, d);
    if (d > 8) bad++;
    const v = d > 8 ? 255 : d * 16;
    out.data[i] = v; out.data[i + 1] = d > 8 ? 0 : v; out.data[i + 2] = d > 8 ? 0 : v; out.data[i + 3] = 255;
  }
  const result = { ref: name, distintos: bad, porcentaje: +((100 * bad) / (W * H)).toFixed(3), max };
  window.__ref = result;
  if (params.get("diff") === "1") sctx.putImageData(out, 0, 0);
  scaler.present(scene);
  drawHud(screen.getContext("2d"), [`ref ${name}: ${bad} píxeles distintos (${result.porcentaje} %), diferencia máx. ${max}`], false);
}

/** Un paso fijo de la simulación (lo usan el bucle y, en debug, __sim.advance). */
function simulate(d) {
  world.now += d;
  demo?.update(world.now);
  world.chars.forEach((c) => c.update(d));
  chatter(world);   // charlas de pasillo cuando dos se cruzan caminando
  updateBg(d);
}

let manual = false;   // __sim.advance pausa el bucle real (si no, su salto de tiempo cuenta como una pausa larga)
if (debug) {
  // Para probar sin esperar (o donde el navegador frena requestAnimationFrame): __sim.advance(10)
  window.__sim = {
    world, bySource, demo, net, onEvent,
    advance(seconds) {
      manual = true;
      for (let t = 0; t < seconds; t += 1 / config.fps) simulate(1 / config.fps);
      render();
    },
    resume() {
      manual = false;
    },
  };
}

if (params.has("ref")) {
  await renderRef(params.get("ref"));
} else {
  // --- bucle ---
  const step = 1 / config.fps;
  let last = performance.now(), acc = 0, frames = 0, fpsT = 0;

  const tick = (t) => {
    requestAnimationFrame(tick);
    let dt = (t - last) / 1000;
    last = t;
    if (manual) return;
    if (dt > 2) {
      // Volvió de una pausa larga (Lively pausado, pestaña oculta): cada uno salta a donde iba
      world.chars.forEach((c) => c.snap());
      dt = step;
    }
    acc += Math.min(dt, 0.1);
    if (acc < step) return;
    const d = acc;
    acc = 0;
    simulate(d);
    render();
    frames++;
    fpsT += d;
    if (fpsT >= 1) {
      fps = frames / fpsT;
      frames = 0;
      fpsT = 0;
    }
  };
  requestAnimationFrame(tick);
}
