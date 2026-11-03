// Demo 30 min simulados con los tres personajes (como main.js ?demo=1&sources=claude,codex,gemini): cuenta choques.
import fs from "fs";
import { pathToFileURL, fileURLToPath } from "url";
let seed = Number(process.argv[2] || 12345) >>> 0;
Math.random = () => { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const fakeCtx = new Proxy({}, { get: () => () => {}, set: () => true });
globalThis.document = { createElement: () => ({ width: 0, height: 0, getContext: () => fakeCtx }) };
const P = fileURLToPath(new URL("../public/", import.meta.url));
const imp = (f) => import(pathToFileURL(P + f).href);
const { Grid, key } = await imp("js/grid.js");
const { World } = await imp("js/sim/world.js");
const { Character } = await imp("js/sim/character.js");
const { Demo } = await imp("js/demo.js");
const { chatter } = await imp("js/sim/chatter.js");
const theme = process.argv[3] || "big_bang";   // node tools/sim_test.mjs [semilla] [tema]
const b = JSON.parse(fs.readFileSync(P + `bundle/${theme}/bundle.json`, "utf8"));
for (const c of Object.values(b.characters)) c.img = { width: 10, height: 10 };
const config = JSON.parse(fs.readFileSync(P + "config.json", "utf8"));
Object.assign(config, config.themes?.[theme] || {});   // como main.js
config.leave_after = config.demo_leave_after ?? 180;
const grid = new Grid(b), world = new World(b, grid, config);
const by = {};
for (const [s, id] of Object.entries(b.cast)) { if (!b.characters[id]) continue; const c = new Character(world, s, id, b.characters[id]); world.add(c); by[s] = c; }
const demo = new Demo((e) => by[e.source]?.handle(e), ["claude", "codex", "gemini"], config.leave_after);
demo.auto = true;
const dt = 1 / config.fps;
let clashes = 0, maxBlocked = 0, says = 0;
const states = {}, places = {};
for (let t = 0; t < 1800; t += dt) {
  world.now += dt; demo.update(world.now);
  for (const c of world.chars) { const before = c.say; c.update(dt); if (c.say && c.say !== before) says++; }
  chatter(world);
  const pres = world.chars.filter((c) => c.present);
  for (const c of pres) {
    if (!isFinite(c.foot[0]) || !isFinite(c.foot[1])) throw new Error("NaN " + c.id);
    states[c.state] = (states[c.state] || 0) + dt; maxBlocked = Math.max(maxBlocked, c.blockedFor);
    if (c.arrived && c.targetKey) places[c.targetKey] = (places[c.targetKey] || 0) + dt;
  }
  const tiles = pres.filter((c) => !c.step && c.alpha >= 1).map((c) => key(...c.tile));
  if (new Set(tiles).size < tiles.length) clashes++;
}
const r = (o) => Object.fromEntries(Object.entries(o).sort().map(([k, v]) => [k, Math.round(v)]));
console.log(JSON.stringify({ seed: process.argv[2] || 12345, clashes, maxBlocked: +maxBlocked.toFixed(2), says, states: r(states), places: r(places) }));
