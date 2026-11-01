// Capas de primer plano (port de Assets BBad/tools/layers.py): muebles y props recortados que se
// redibujan encima de quien queda detrás. El fondo ya los tiene pintados; solo se redibujan los que tapan a alguien.

import { key } from "./grid.js";

export function prepare(layers) {
  for (const l of layers) {
    l.tileSet = new Set(l.tiles.map(([a, b]) => key(a, b)));
    l.box = [l.pos[0], l.pos[1], l.pos[0] + l.size[0], l.pos[1] + l.size[1]];
  }
  return layers;
}

/** true si el mueble queda delante de un personaje en la casilla (a, b). */
export function covers(layer, [a, b]) {
  if (layer.tileSet.has(key(a, b))) return false;
  return layer.tiles.some(([la, lb]) => la >= a && lb >= b);
}

const overlap = (p, q) => p[0] < q[2] && q[0] < p[2] && p[1] < q[3] && q[1] < p[3];

/**
 * Dibuja los personajes y encima los muebles que los tapan, en orden topológico (como layers.compose).
 * actors: [{box: [x0, y0, x1, y1], tile: [a, b], draw(ctx)}]; drawLayer(ctx, layer) pinta un mueble.
 */
export function compose(ctx, layers, actors, drawLayer) {
  const active = layers.filter((l) => actors.some((a) => overlap(l.box, a.box) && covers(l, a.tile)));
  const items = [
    ...actors.map((a) => ({ kind: "actor", it: a, box: a.box, foot: a.box[3] })),
    ...active.map((l) => ({ kind: "layer", it: l, box: l.box, foot: l.box[3] })),
  ];
  const n = items.length;
  const after = items.map(() => new Set());
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const x = items[i], y = items[j];
      if (!overlap(x.box, y.box)) continue;
      let front;
      if (x.kind === "actor" && y.kind === "actor") front = y.foot >= x.foot ? j : i;
      else if (x.kind === "layer" && y.kind === "layer") front = y.it.depth >= x.it.depth ? j : i;
      else {
        const [act, lay, ia, il] = x.kind === "actor" ? [x, y, i, j] : [y, x, j, i];
        front = covers(lay.it, act.it.tile) ? il : ia;
      }
      after[front === j ? i : j].add(front);
    }
  }
  // Orden topológico; si hay un ciclo, sigue por el de pies más abajo
  const pending = new Array(n).fill(0);
  for (const s of after) for (const j of s) pending[j]++;
  const done = new Set();
  while (done.size < n) {
    let pick = -1;
    for (const onlyReady of [true, false]) {
      for (let i = 0; i < n; i++) {
        if (done.has(i) || (onlyReady && pending[i] !== 0)) continue;
        if (pick < 0 || items[i].foot < items[pick].foot) pick = i;
      }
      if (pick >= 0) break;
    }
    done.add(pick);
    for (const j of after[pick]) pending[j]--;
    const { kind, it } = items[pick];
    if (kind === "actor") it.draw(ctx);
    else drawLayer(ctx, it);
  }
}
