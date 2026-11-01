// Mundo de la simulación: lugares, asientos con dueño y quién ocupa o reclama cada lugar y casilla.

import { key } from "../grid.js";

export class World {
  constructor(bundle, grid, config) {
    this.b = bundle;
    this.grid = grid;
    this.config = config;
    this.places = bundle.places;
    this.chars = [];
    this.claims = new Map();   // lugar -> personaje que lo reclamó (el dueño que viene a sentarse)
    this.special = null;       // escena especial en curso (Flash, Frodo): una sola a la vez
    this.specialEnd = -Infinity; // cuándo terminó la última especial (para scenes.special_gap)
    this.tint = 0;             // "mundo de las sombras" de Frodo: 0..1 de gris y oscuro
    this.fx = [];              // chispas y destellos: {kind, t0, x, y, seed}
    this.now = 0;
  }

  add(ch) {
    this.chars.push(ch);
  }

  get anyPresent() {
    return this.chars.some((c) => c.present);
  }

  /** Datos de un lugar del tema, o de una casilla suelta "@a,b" o "@a,b/dirección" (paseos, esperas, escenas). */
  place(name) {
    if (name.startsWith("@")) {
      const [t, facing] = name.slice(1).split("/");
      const tile = t.split(",").map(Number);
      return { tile, facing: facing || null, foot: this.grid.center(...tile) };
    }
    return this.places[name];
  }

  /** Grupo de asientos al que lleva un lugar o rol (couch, desk), o null. */
  seatGroup(name) {
    const role = this.b.roles[name];
    if (!(name in this.places) && role) name = role.place;
    return this.b.seats[name] ? name : null;
  }

  /**
   * Lugar concreto de un lugar, rol o grupo de asientos (port de theme.place_key): si el personaje tiene
   * asientos permitidos en el grupo (only), el primero libre de esos; si no, el asiento propio (owners),
   * el que le gusta aunque sea de otro (prefers), uno libre sin dueño o el primero libre.
   */
  placeKey(name, who, taken = new Set()) {
    const role = this.b.roles[name];
    if (!(name in this.places) && role) name = role.place;
    const seats = this.b.seats[name];
    if (!seats) return name;
    const only = this.b.only?.[who]?.[name];
    if (only) return only.find((s) => !taken.has(s)) ?? only[0];
    const owners = this.b.owners;
    let free = seats.filter((s) => !taken.has(s));
    if (!free.length) free = seats;
    const mine = free.filter((s) => owners[s] === who);
    const liked = free.filter((s) => (this.b.prefers?.[who] || []).includes(s));
    const unowned = free.filter((s) => !(s in owners));
    return (mine.length ? mine : liked.length ? liked : unowned.length ? unowned : free)[0];
  }

  /**
   * Para el que tiene que dejar un asiento ajeno (disputa): el asiento más cercano del mismo grupo, sin
   * dueño o suyo, si está libre ({place, group}); si no, null y elige como siempre (Penny: la banqueta).
   */
  asideSeat(seat, ch) {
    const group = Object.keys(this.b.seats).find((g) => Array.isArray(this.b.seats[g]) && this.b.seats[g].includes(seat));
    if (!group) return null;
    const t = this.places[seat].tile;
    const owners = this.b.owners || {};
    const dist = (s) => Math.abs(this.places[s].tile[0] - t[0]) + Math.abs(this.places[s].tile[1] - t[1]);
    const near = this.b.seats[group].filter((s) => s !== seat && (!(s in owners) || owners[s] === ch.id))
      .sort((a, b) => dist(a) - dist(b))[0];
    return near && !this.takenPlaces(ch).has(near) ? { place: near, group } : null;
  }

  /** Lugares a los que van (o en los que están) los demás, y los que reclamó otro. */
  takenPlaces(except) {
    const out = new Set(this.chars.filter((c) => c !== except && c.present && c.targetKey).map((c) => c.targetKey));
    for (const [place, c] of this.claims) if (c !== except) out.add(place);
    return out;
  }

  /** Otro personaje que está en ese lugar o va hacia él. */
  occupant(place, except) {
    return this.chars.find((c) => c !== except && c.present && c.targetKey === place) || null;
  }

  /** Si un lugar es un asiento (de un grupo o permitido a alguien, como la banqueta de la cocina). */
  isSeat(place) {
    const lists = [...Object.values(this.b.seats), ...Object.values(this.b.only || {}).flatMap((o) => Object.values(o))];
    return lists.some((s) => s.includes(place));
  }

  claim(place, ch) {
    this.claims.set(place, ch);
  }

  release(ch) {
    for (const [place, c] of this.claims) if (c === ch) this.claims.delete(place);
  }

  /** Casillas ocupadas por los demás: donde están parados y la siguiente de su paso. */
  blockedTiles(except) {
    const out = new Set();
    for (const c of this.chars) {
      if (c === except || !c.present) continue;
      out.add(key(...c.tile));
      if (c.step) out.add(key(...c.step.to));
    }
    return out;
  }

  /** Casilla caminable libre más cercana a tile (BFS), sin contar las de exclude. */
  freeTileNear(tile, exclude, except) {
    const blocked = this.blockedTiles(except);
    const seen = new Set([key(...tile)]);
    const queue = [tile];
    for (let i = 0; i < queue.length; i++) {
      const t = queue[i];
      const k = key(...t);
      if (this.grid.walkable.has(k) && !blocked.has(k) && !exclude.has(k)) return t;
      for (const f of Object.values(this.grid.facings)) {
        const n = [t[0] + f.step[0], t[1] + f.step[1]];
        const nk = key(...n);
        if (!seen.has(nk) && (this.grid.walkable.has(nk) || i === 0)) {
          seen.add(nk);
          queue.push(n);
        }
      }
    }
    return null;
  }
}
