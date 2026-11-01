// Grilla isométrica de casillas (port de Assets BBad/tools/grid.py).
// Los pies en el centro de cada casilla vienen precalculados en el bundle (mismo redondeo que Python).

export const key = (a, b) => `${a},${b}`;

export class Grid {
  constructor(bundle) {
    const g = bundle.grid;
    this.origin = g.origin;
    this.u = g.u;
    this.v = g.v;
    this.walkable = new Set(bundle.walkable.map(([a, b]) => key(a, b)));
    this.tiles = bundle.walkable;
    this.centers = bundle.centers;
    // Mismo orden que FACINGS en grid.py: el BFS da el mismo camino que en Python
    this.facings = bundle.facings;
  }

  corner(a, b) {
    return [this.origin[0] + a * this.u[0] + b * this.v[0], this.origin[1] + a * this.u[1] + b * this.v[1]];
  }

  /** Punto donde van los pies en la casilla (a, b). */
  center(a, b) {
    const c = this.centers[key(a, b)];
    if (c) return c;
    const [x, y] = this.corner(a + 0.5, b + 0.5);
    return [Math.round(x), Math.round(y)];
  }

  polygon(a, b) {
    return [[0, 0], [1, 0], [1, 1], [0, 1]].map(([da, db]) => this.corner(a + da, b + db));
  }

  /** Camino más corto de casilla en casilla (sin contar start), o null. start y goal pueden no ser caminables. */
  path(start, goal, blocked = new Set()) {
    const goalKey = key(...goal);
    const prev = new Map([[key(...start), null]]);
    const queue = [start];
    for (let i = 0; i < queue.length; i++) {
      const cur = queue[i];
      const ck = key(...cur);
      if (ck === goalKey) {
        const out = [];
        for (let k = ck, t = cur; k !== key(...start); t = prev.get(k), k = key(...t)) out.push(t);
        return out.reverse();
      }
      for (const f of Object.values(this.facings)) {
        const nxt = [cur[0] + f.step[0], cur[1] + f.step[1]];
        const nk = key(...nxt);
        if (!prev.has(nk) && ((this.walkable.has(nk) && !blocked.has(nk)) || nk === goalKey)) {
          prev.set(nk, cur);
          queue.push(nxt);
        }
      }
    }
    return null;
  }

  /** Dirección de pantalla de un paso entre casillas vecinas. */
  facingOf(da, db) {
    for (const [name, f] of Object.entries(this.facings)) {
      if (f.step[0] === da && f.step[1] === db) return name;
    }
    throw new Error(`paso no válido: ${da},${db}`);
  }
}
