// Guiones: escenas que toman el control de un personaje un rato y después lo devuelven a su rol.
// Cada guion es un generador de comandos que ejecuta Character.runScript:
//   {kind: "walk", to, speed?, anims?}   caminar a un lugar o casilla ("@a,b")
//   {kind: "play", anim, seconds}        reproducir una animación (seconds 0: solo la pone)
//   {kind: "fade", to, seconds}          aparecer (1) o desaparecer (0)
//   {kind: "wait", seconds} · {kind: "face", facing} · {kind: "swap", costume} · {kind: "trail", on}
//   {kind: "say", text, seconds}         globo de diálogo (no espera)
//   {kind: "until", cond, timeout}       esperar a que pase algo
//   {kind: "call", fn}                   hacer algo (por ejemplo, arrancar el guion de otro)
//   {kind: "dither", to, seconds, tint?, sparks?}  aparecer (1) o disolverse (0) con tramado; tint: la escena
//                                        se va al gris mientras no se lo ve; sparks: chispas doradas
//   {kind: "jump", tile, facing}         pasar a otra casilla sin caminar (invisible)
//   {kind: "glint"}                      destello del Anillo (en el píxel dorado de ring_on)

import { key } from "../grid.js";
import { covers } from "../layers.js";

const RUN = { three_quarter: "flash_run", back: "flash_run_back" };
const name = (id) => id[0].toUpperCase() + id.slice(1);
const REPLY = { penny: "¡Ok, ok!", leonard: "Bueno, bueno...", sheldon: "Hmm." };
// Dirección para mirar de frente a un lugar que mira hacia otro lado
const OPPOSITE = { down_right: "up_left", down_left: "up_right", up_right: "down_left", up_left: "down_right" };

/** Sheldon es Flash (BIG_BANG.md §6, como flash_preview.py): la puerta, el traje, correr con estela y volver. */
export function* flash(ch) {
  const cfg = ch.config.scenes.flash;
  yield { kind: "walk", to: "door" };
  yield { kind: "fade", to: 0, seconds: 0.4 };
  yield { kind: "wait", seconds: 1 };
  yield { kind: "swap", costume: "flash" };
  yield { kind: "face", facing: "down_right" };
  yield { kind: "play", anim: "flash_pose", seconds: 0 };
  yield { kind: "fade", to: 1, seconds: 0.15 };
  yield { kind: "play", anim: "flash_pose", seconds: 1.5 };
  yield { kind: "trail", on: true };
  for (const [a, b] of cfg.route) yield { kind: "walk", to: `@${a},${b}`, speed: cfg.speed, anims: RUN };
  yield { kind: "face", facing: "down_right" };
  yield { kind: "play", anim: "flash_pose", seconds: 2 };
  yield { kind: "play", anim: "flash_idle", seconds: 1.5 };
  yield* flashHome(ch);
}

/** Final de Flash (también si lo corta un evento): corre a la puerta, se cambia y vuelve a ser Sheldon. */
export function* flashHome(ch) {
  if (ch.costume !== "flash") return;
  yield { kind: "trail", on: true };
  yield { kind: "walk", to: "door", speed: ch.config.scenes.flash.speed, anims: RUN };
  yield { kind: "fade", to: 0, seconds: 0.1 };
  yield { kind: "trail", on: false };
  yield { kind: "wait", seconds: 0.5 };
  yield { kind: "swap", costume: null };
  yield { kind: "face", facing: "down_right" };
  yield { kind: "fade", to: 1, seconds: 0.3 };
}

/** El dueño encuentra a otro en su asiento: se para enfrente, le dice que es su lugar y espera que se vaya. */
export function* seatDispute(ch, other, seat) {
  const w = ch.world;
  const p = w.place(seat);
  const step = w.grid.facings[p.facing].step;
  const front = [p.tile[0] + step[0], p.tile[1] + step[1]];
  // Un paso más hacia la cámara, para no tapar el camino de salida del asiento
  const spot = w.freeTileNear([front[0] + step[0], front[1] + step[1]], new Set([key(...front)]), ch) || front;
  w.claim(seat, ch);
  yield { kind: "walk", to: `@${spot[0]},${spot[1]}/${OPPOSITE[p.facing]}` };
  yield { kind: "play", anim: ch.anims.argue ? "argue" : null, seconds: 0 };
  yield { kind: "say", text: `${name(other.id)}... ese es mi lugar.`, seconds: 2.6 };
  yield { kind: "wait", seconds: 1.8 };
  yield { kind: "call", fn: () => other.startScript(moveAside(other, seat)) };
  // Hasta que se fue de verdad: otro destino y ya fuera del asiento y de la casilla de enfrente
  const at = (t) => other.tile[0] === t[0] && other.tile[1] === t[1];
  yield { kind: "until", cond: () => !other.present || (other.targetKey !== seat && !at(p.tile) && !at(front)), timeout: 8 };
  yield { kind: "wait", seconds: 0.3 };
}

/**
 * Quien estaba en el lugar ajeno contesta y se corre al asiento de al lado si está libre (Penny: el del
 * medio del sillón, aunque no esté entre los suyos); si no, a otro como siempre (el reclamado ya no le sale libre).
 */
export function* moveAside(ch, seat) {
  yield { kind: "play", anim: ch.anims.argue ? "argue" : null, seconds: 0 };
  yield { kind: "say", text: REPLY[ch.id] ?? "Perdón.", seconds: 1.6 };
  yield { kind: "wait", seconds: 1.2 };
  // Al terminar el guion vuelve a su rol: goTo usa este asiento mientras el rol siga en el mismo grupo
  ch.aside = seat ? ch.world.asideSeat(seat, ch) : null;
}

const BOARD_ASK = { penny: "Penny, ¿qué estás haciendo con mi pizarrón?" };
const BOARD_REPLY = { penny: "Nada..." };

/**
 * Sheldon encuentra a otro en un lugar compartido que es "suyo" (config.place_disputes: el pizarrón): se le
 * para atrás, le pregunta qué hace y espera a que se vaya; después el guion termina y él va al lugar.
 */
export function* placeDispute(ch, other, place) {
  const w = ch.world;
  const p = w.place(place);
  // Atrás del otro (del lado de la cámara), mirando para el mismo lado que él
  const back = w.grid.facings[OPPOSITE[p.facing]].step;
  const spot = w.freeTileNear([p.tile[0] + back[0], p.tile[1] + back[1]], new Set([key(...p.tile)]), ch);
  w.claim(place, ch);
  if (spot) yield { kind: "walk", to: `@${spot[0]},${spot[1]}/${p.facing}` };
  yield { kind: "say", text: BOARD_ASK[other.id] ?? `${name(other.id)}, ¿qué estás haciendo?`, seconds: 2.8 };
  yield { kind: "wait", seconds: 2 };
  // Si mientras tanto ya se fue solo (otro evento), no hace falta que conteste
  yield { kind: "call", fn: () => { if (!other.script && other.targetKey === place) other.startScript(leavePlace(other, place), false); } };
  const at = (t) => other.tile[0] === t[0] && other.tile[1] === t[1];
  yield { kind: "until", cond: () => !other.present || (other.targetKey !== place && !at(p.tile)), timeout: 8 };
  yield { kind: "wait", seconds: 0.3 };
}

/** El echado del lugar compartido se da vuelta, contesta y se va a su asiento de reposo (ahí espera, ver goTo). */
export function* leavePlace(ch, place) {
  const w = ch.world;
  const p = w.place(place);
  yield { kind: "face", facing: OPPOSITE[p.facing] };
  yield { kind: "play", anim: ch.anims.argue ? "argue" : null, seconds: 0 };
  yield { kind: "say", text: BOARD_REPLY[ch.id] ?? "Nada, nada...", seconds: 1.6 };
  yield { kind: "wait", seconds: 1.2 };
  // Al terminar el guion goTo la deja ahí (displaced) mientras by tenga el lugar
  yield { kind: "walk", to: w.placeKey("rest", ch.id, w.takenPlaces(ch)) };
}

/** Paseo en reposo: una o dos vueltas por lugares del living o casillas libres, y vuelve a su asiento. */
export function* wander(ch, rand = Math.random) {
  const w = ch.world;
  const cfg = ch.config.scenes.wander;
  const laps = 1 + Math.floor(rand() * 2);
  for (let i = 0; i < laps; i++) {
    let to = null;
    if (rand() < 0.5) {
      const name = cfg.places[Math.floor(rand() * cfg.places.length)];
      if (!w.occupant(name, ch)) to = name;
    }
    if (!to) {
      const tiles = w.grid.tiles;
      const t = tiles[Math.floor(rand() * tiles.length)];
      // Nunca en la casilla de un lugar: en la van los lugares de reposo son del piso y otro puede ir para ahí
      const places = new Set(Object.values(w.b.places).map((p) => key(...p.tile)));
      const free = w.freeTileNear(t, places, ch);
      if (free) to = `@${free[0]},${free[1]}/${rand() < 0.5 ? "down_right" : "down_left"}`;
    }
    if (!to) break;
    yield { kind: "walk", to };
    yield { kind: "play", anim: null, seconds: cfg.stay[0] + rand() * (cfg.stay[1] - cfg.stay[0]) };
  }
}

/** Sheldon juega al bowling de la Wii: se para detrás de la tele (le tapa las piernas), de frente, unas tiradas. */
export function* playWii(ch, rand = Math.random) {
  const cfg = ch.config.scenes.wii;
  const a = ch.anims.wii;
  const throws = cfg.throws[0] + Math.floor(rand() * (cfg.throws[1] - cfg.throws[0] + 1));
  yield { kind: "walk", to: cfg.place };
  yield { kind: "face", facing: "down_right" };
  yield { kind: "play", anim: "wii", seconds: throws * a.frames.length / a.fps };
  yield { kind: "play", anim: null, seconds: 0.8 };
}

/**
 * Sheldon se tapa con la manta y teclea en la notebook sentado en el sillón (BIG_BANG.md §6): blanket_on,
 * blanket_type en loop y blanket_off. hold: mientras devuelva true sigue tecleando (para cuando la IA esté
 * en uso alto); sin hold, cfg.type segundos al azar (la prueba en reposo).
 */
export function* blanket(ch, rand = Math.random, hold = null) {
  const cfg = ch.config.scenes.blanket;
  const t = (name) => ch.anims[name].frames.length / ch.anims[name].fps;
  ch.blanketOn = true;
  yield { kind: "play", anim: "blanket_on", seconds: t("blanket_on") };
  if (hold) {
    yield { kind: "play", anim: "blanket_type", seconds: 0 };
    yield { kind: "until", cond: () => !hold(), timeout: Infinity };
  } else {
    // cfg.type: [min, max] o varios rangos (un rato corto o uno largo), uno al azar
    const ranges = Array.isArray(cfg.type[0]) ? cfg.type : [cfg.type];
    const [lo, hi] = ranges[Math.floor(rand() * ranges.length)];
    yield { kind: "play", anim: "blanket_type", seconds: lo + rand() * (hi - lo) };
  }
  yield* blanketOff(ch);
}

/** Final de la manta (también si lo corta un evento): cierra la notebook y se saca la manta. */
export function* blanketOff(ch) {
  if (!ch.blanketOn) return;
  yield { kind: "play", anim: "blanket_off", seconds: ch.anims.blanket_off.frames.length / ch.anims.blanket_off.fps };
  ch.blanketOn = false;
  yield { kind: "play", anim: "sit", seconds: 0.5 };
}

// Mirar hacia la cámara del mismo lado (las animaciones de hobbit son de 3/4 de frente)
const FRONT = { up_right: "down_right", up_left: "down_left", down_right: "down_right", down_left: "down_left" };

/** Leonard es Frodo (BIG_BANG.md §6, como frodo_preview.py): el pasillo, el disfraz, el Anillo y los saltos. */
export function* frodo(ch, rand = Math.random) {
  const cfg = ch.config.scenes.hobbit;
  const hall = ch.world.place("hallway").tile;
  yield { kind: "walk", to: "hallway" };
  yield { kind: "dither", to: 0, seconds: 0.5 };
  yield { kind: "wait", seconds: 1.2 };
  yield { kind: "swap", costume: "hobbit" };
  yield { kind: "face", facing: "down_left" };
  yield { kind: "dither", to: 1, seconds: 0.5 };
  yield { kind: "wait", seconds: 0.6 };
  let cur = farTile(ch, hall, cfg.min_jump, rand);
  if (!cur) return yield* frodoHome(ch);
  yield { kind: "walk", to: `@${cur[0]},${cur[1]}` };
  const ring = ch.anims.ring_on;
  const ringT = ring.frames.length / ring.fps;
  const jumps = cfg.jumps[0] + Math.floor(rand() * (cfg.jumps[1] - cfg.jumps[0] + 1));
  for (let i = 0; i < jumps; i++) {
    // Se pone el Anillo: destello en el último cuadro; se disuelve con chispas y la escena se va al gris
    yield { kind: "face", facing: FRONT[ch.facing] };
    yield { kind: "wait", seconds: 0.6 };
    yield { kind: "play", anim: "ring_on", seconds: ringT };
    yield { kind: "glint" };
    yield { kind: "wait", seconds: 0.5 };
    yield { kind: "dither", to: 0, seconds: 0.5, tint: true, sparks: true };
    yield { kind: "wait", seconds: 1.3 };
    // Reaparece lejos, todavía con el Anillo, y se lo saca
    const nxt = farTile(ch, cur, cfg.min_jump, rand);
    if (nxt) cur = nxt;
    yield { kind: "jump", tile: cur, facing: rand() < 0.5 ? "down_left" : "down_right" };
    yield { kind: "dither", to: 1, seconds: 0.5, tint: true, sparks: true };
    yield { kind: "wait", seconds: 0.6 };
    yield { kind: "play", anim: "ring_off", seconds: ringT };
  }
  yield { kind: "play", anim: null, seconds: 0.8 };
  yield* frodoHome(ch);
}

/** Final de Frodo (también si lo corta un evento): vuelve visible, va al pasillo y reaparece como Leonard. */
export function* frodoHome(ch) {
  if (ch.costume !== "hobbit") return;
  if (ch.vis < 1) yield { kind: "dither", to: 1, seconds: 0.4, tint: ch.world.tint > 0 };
  yield { kind: "walk", to: "hallway" };
  yield { kind: "dither", to: 0, seconds: 0.5 };
  yield { kind: "wait", seconds: 1 };
  yield { kind: "swap", costume: null };
  yield { kind: "face", facing: "down_left" };
  yield { kind: "dither", to: 1, seconds: 0.5 };
  yield { kind: "wait", seconds: 0.5 };
}

/**
 * Casilla libre al azar lejos de frm (a + b >= minJump) y a la vista: ni un lugar del tema, ni donde un
 * mueble lo taparía (como far_tile y hidden_tiles de frodo_preview.py).
 */
function farTile(ch, frm, minJump, rand) {
  const w = ch.world;
  const a = ch.anims.idle || ch.anims.ref_three_quarter;
  const [, , sw, sh] = a.frames[0];
  const places = new Set(Object.values(w.places).map((p) => key(...p.tile)));
  const blocked = w.blockedTiles(ch);
  const ok = w.grid.tiles.filter((t) => {
    const k = key(...t);
    if (places.has(k) || blocked.has(k) || Math.abs(t[0] - frm[0]) + Math.abs(t[1] - frm[1]) < minJump) return false;
    const [x, y] = w.grid.center(...t);
    const box = [x - sw / 2, y - sh, x + sw / 2, y];
    return !w.b.layers.some((l) => covers(l, t) && box[0] < l.box[2] && l.box[0] < box[2] && box[1] < l.box[3] && l.box[1] < box[3]);
  });
  return ok.length ? ok[Math.floor(rand() * ok.length)] : null;
}
