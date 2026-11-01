// Un personaje (una IA): máquina de estados de IDEA_Y_ANIMACION.md §5 y movimiento de casilla en casilla.
//
// ABSENT -> ENTERING (aparece en la puerta o en su "home" y camina al lugar de su rol)
// IDLE (rest) / THINKING (think) / WORKING (shell, edit, read, web) según el último evento
// LEAVING: sin eventos un rato se va a su home (Sheldon y Leonard: el pasillo); al cerrar la sesión, por la puerta.
// SCRIPTED: lo maneja un guion (scenes.js): paseo, disputa por el asiento, Flash...

import { key } from "../grid.js";
import { greetTalk } from "./chatter.js";
import { blanket, blanketOff, flash, flashHome, frodo, frodoHome, placeDispute, playWii, seatDispute, wander } from "./scenes.js";

const ROLE_STATE = { rest: "IDLE", think: "THINKING" };
const WALK = { three_quarter: "walk", back: "walk_back" };
// Al aparecer en un lugar que mira hacia el fondo (el pasillo), mira hacia el living
const TURN = { up_right: "down_left", up_left: "down_right", down_left: "up_right" };
const TRAIL = 6;
// Escenas especiales por disfraz (config.costumes): guion y final si lo corta un evento
const SPECIALS = { flash: [flash, flashHome], hobbit: [frodo, frodoHome] };
// Tramado Bayer 4x4 fijo a la pantalla (frodo_preview.dither)
const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
const ditherCanvas = document.createElement("canvas");

/**
 * Actor para layers.compose: un cuadro de una animación del atlas con los pies en foot.
 * Espejado, el ancla pasa a w - 1 - ax (como walk_preview.hold).
 */
export function spriteActor(img, anim, frame, foot, tile, flip, alpha = 1, vis = 1) {
  const [sx, sy, w, h] = anim.frames[frame];
  const ax = flip ? w - 1 - anim.anchor[0] : anim.anchor[0];
  const x = Math.round(foot[0] - ax), y = Math.round(foot[1] - anim.anchor[1]);
  return {
    box: [x, y, x + w, y + h],
    tile,
    draw(ctx) {
      ctx.save();
      ctx.globalAlpha = alpha;
      if (vis < 1) {
        // Solo una fracción vis de los píxeles (tramado): se arma en un canvas aparte
        const c = ditherCanvas;
        c.width = w;
        c.height = h;
        const g = c.getContext("2d", { willReadFrequently: true });
        if (flip) {
          g.translate(w, 0);
          g.scale(-1, 1);
        }
        g.drawImage(img, sx, sy, w, h, 0, 0, w, h);
        const d = g.getImageData(0, 0, w, h);
        for (let py = 0; py < h; py++) {
          const row = BAYER[(((py + y) % 4) + 4) % 4];
          for (let px = 0; px < w; px++) if (row[(((px + x) % 4) + 4) % 4] >= vis * 16) d.data[(py * w + px) * 4 + 3] = 0;
        }
        g.putImageData(d, 0, 0);
        ctx.drawImage(c, x, y);
      } else if (flip) {
        ctx.translate(x + w, y);
        ctx.scale(-1, 1);
        ctx.drawImage(img, sx, sy, w, h, 0, 0, w, h);
      } else {
        ctx.drawImage(img, sx, sy, w, h, x, y, w, h);
      }
      ctx.restore();
    },
  };
}

/** Atlas "fantasma" para la estela: difuminado y teñido hacia rojo / amarillo (como walk_preview.ghost). */
function ghostAtlas(img) {
  const c = document.createElement("canvas");
  c.width = img.width + 4;
  c.height = img.height + 4;
  const g = c.getContext("2d");
  g.filter = "blur(1.2px)";
  g.drawImage(img, 0, 0);
  g.filter = "none";
  g.globalCompositeOperation = "source-atop";
  g.fillStyle = "rgba(255, 150, 30, 0.45)";
  g.fillRect(0, 0, c.width, c.height);
  return c;
}

export function toolRole(tool, config) {
  const t = (tool || "").toLowerCase();
  if (t.startsWith("mcp__")) return "web";
  return config.tool_roles[t] ?? "edit";
}

export class Character {
  constructor(world, source, id, data) {
    this.world = world;
    this.source = source;
    this.id = id;
    this.base = data;
    this.img = data.img;
    this.anims = data.anims;
    this.costume = null;
    this.present = false;
    this.state = "ABSENT";
    this.tile = [0, 0];
    this.foot = [0, 0];
    this.facing = "down_right";
    this.route = [];
    this.step = null;            // paso en curso: {from, fromTile, to, toFoot, p}
    this.wait = 0;
    this.blockedFor = 0;
    this.targetKey = null;       // lugar concreto al que va o en el que está
    this.targetRole = null;      // rol por el que fue ahí
    this.aside = null;           // {place, group}: asiento al que se corrió cuando lo echaron (moveAside)
    this.displaced = null;       // {place, by}: lo echaron de un lugar compartido (placeDispute); espera en su asiento
    this.arrived = false;
    this.arrivedAt = 0;
    this.role = "rest";          // rol que pide el último evento
    this.leaving = null;         // "door" | "home" mientras se va
    this.exit = this.outside;    // por dónde se fue la última vez (por ahí vuelve)
    this.alpha = 1;
    this.vis = 1;                // fracción de píxeles que se ven (tramado de Frodo)
    this.fadeDir = 0;
    this.anim = "idle";
    this.animT = 0;
    this.lastEvent = 0;
    this.graceUntil = null;
    this.speed = null;           // velocidad y animaciones de caminar de un guion (null: las normales)
    this.walkAnims = WALK;
    this.script = null;          // {gen, onAbort}
    this.cmd = null;
    this.abort = false;
    this.trailOn = false;
    this.trail = [];
    this.say = null;             // globo: {text, until}
    this.box = null;             // último rectángulo dibujado (para el globo)
    this.nextCheck = 0;          // próximo sorteo de paseo / escena especial
    this.cooldowns = {};
    this.greet = null;           // "enter" | "leave": falta el saludo de la entrada o de la puerta al irse
    this.waveUntil = 0;          // saludando (quieto) hasta esta hora
  }

  get config() {
    return this.world.config;
  }

  get home() {
    const h = this.config.home?.[this.id];
    return h && h in this.world.places ? h : this.outside;
  }

  /** Por dónde entra y sale al abrir y cerrar su programa: la esquina de adelante a la izquierda (exit). */
  get outside() {
    return "exit" in this.world.places ? "exit" : "door";
  }

  // --- eventos ---

  handle(ev) {
    const now = this.world.now;
    this.lastEvent = now;
    if (ev.effort) this.effort = ev.effort;
    if (ev.type === "session_end") {
      this.role = "rest";   // ya no trabaja (ni en uso alto)
      if (this.present && !this.leaving) {
        if (this.script) {
          // Se va por la puerta cuando termine el final del guion (la manta, la vuelta de Flash...)
          this.abort = true;
          this.leaveAfterScript = "door";
        } else this.leave("door");
      }
      return;
    }
    this.leaveAfterScript = null;   // volvió antes de que terminara el guion
    if (ev.type === "request_start") this.role = "think";
    else if (ev.type === "tool_call") this.role = toolRole(ev.tool, this.config);
    else if (ev.type === "turn_end") this.role = "rest";
    this.graceUntil = ev.type === "tool_result" ? now + this.config.think_grace : null;

    if (this.script) {
      // Un evento corta el guion (paseo, Flash) en su siguiente punto seguro; las discusiones terminan solas
      if (this.script.interruptible) this.abort = true;
      return;
    }
    if (!this.present) this.enter(ev.type === "session_start" ? this.outside : this.exit);
    else if (this.leaving) {
      // Vuelve antes de irse del todo
      this.leaving = null;
      if (this.fadeDir < 0 || this.alpha < 1) this.fadeDir = 1;
      this.state = "ENTERING";
      this.targetRole = null;
    }
  }

  enter(from) {
    const p = this.world.place(from);
    this.present = true;
    this.leaving = null;
    this.state = "ENTERING";
    this.tile = [...p.tile];
    this.foot = [...p.foot];
    this.facing = TURN[p.facing] ?? p.facing;
    this.route = [];
    this.step = null;
    this.targetKey = from;
    this.targetRole = null;
    this.arrived = true;
    this.arrivedAt = this.world.now;
    this.alpha = 0;
    this.fadeDir = 1;
    this.greet = "enter";
    this.setAnim(this.standAnim(false));
  }

  /**
   * Al terminar de aparecer, o en la puerta antes de irse: frase (chatter.greetTalk) y, si hay alguien,
   * saludo con la mano (wave). Al irse se queda lo que dura el globo, así se lee, y después desaparece.
   */
  greeting(now) {
    const kind = this.greet;
    this.greet = null;
    if (kind === "leave" && this.leaving !== "door") return;   // volvió antes de irse
    const someone = greetTalk(this.world, this, kind);
    const a = someone ? this.anims.wave : null;
    if (a) this.setAnim("wave");
    const dur = a ? a.frames.length / a.fps : 0;
    this.waveUntil = now + (kind === "leave" ? Math.max(dur, this.config.chatter?.seconds ?? 2.6) : dur);
  }

  leave(mode) {
    this.leaving = mode;
    this.state = "LEAVING";
    this.graceUntil = null;
    this.goTo(mode === "door" ? this.outside : this.home, null);
  }

  // --- movimiento ---

  goTo(name, role) {
    const w = this.world;
    // Mi asiento ocupado por otro: si ya está sentado, discusión; si va en camino, que busque otro
    const group = role ? w.seatGroup(name) : null;
    // Solo los de "disputes" reclaman (Sheldon); los demás, si ya se sentó otro, buscan otro asiento
    const own = group && (this.config.disputes || []).includes(this.id)
      && w.b.seats[group].find((s) => w.b.owners[s] === this.id);
    if (own) {
      const other = w.occupant(own, this);
      // (si está ahí solo esperando a que le devuelvan el pizarrón, displaced, se va sin discusión)
      if (other && other.arrived && !other.script && other.alpha >= 1 && !other.displaced) {
        this.startScript(seatDispute(this, other, own), false);
        return;
      }
      if (other) {
        w.claim(own, this);
        other.targetRole = null;
      }
    }
    const taken = w.takenPlaces(this);
    if (own && w.claims.get(own) === this) taken.delete(own);   // el que va hacia ahí ya lo está dejando
    let k = w.placeKey(name, this.id, taken);
    // Lo echaron de un asiento ajeno (moveAside): se queda en el de al lado mientras el rol siga en ese
    // grupo y nadie se lo tome; con otro rol (o si se lo ocuparon) vuelven las reglas de siempre
    if (role && this.aside) {
      if (group === this.aside.group && !taken.has(this.aside.place)) k = this.aside.place;
      else this.aside = null;
    }
    // Lugar compartido "de" alguien (config.place_disputes: el pizarrón de Sheldon): echa a los de su lista;
    // al echado lo manda a su asiento de reposo mientras el otro lo tenga (no espera al lado)
    if (role && !group && !k.startsWith("@")) {
      const rule = this.config.place_disputes?.[k];
      const other = w.occupant(k, this);
      if (other && !other.script && (rule?.[this.id] || []).includes(other.id)) {
        if (other.arrived && other.alpha >= 1) {
          this.startScript(placeDispute(this, other, k), false);
          return;
        }
        // Todavía iba para ahí: el lugar es mío y él se va a otro lado sin discusión
        w.claim(k, this);
        other.goTo(other.role, other.role);
      }
      const claimer = w.claims.get(k);
      const boss = claimer && claimer !== this ? claimer : w.occupant(k, this);
      this.displaced = boss && (rule?.[boss.id] || []).includes(this.id) ? { place: k, by: boss } : null;
      if (this.displaced) k = w.placeKey("rest", this.id, taken);
    } else if (role) this.displaced = null;
    // Lugar compartido (pizarrón, ventana...) que ya tiene otro: espera al lado, mirando para el mismo lado
    if (!group && !k.startsWith("@") && role && w.occupant(k, this)) {
      const p = w.place(k);
      const near = w.freeTileNear(p.tile, new Set(w.chars.map((c) => c.targetKey).filter(Boolean)
        .map((t) => key(...w.place(t).tile))), this);
      if (near) k = `@${near[0]},${near[1]}/${p.facing}`;
    }
    // Cambió de idea (movimiento normal, no un guion): suelta lo que había reclamado
    if (role) for (const [place, c] of w.claims) if (c === this && place !== k) w.claims.delete(place);
    this.targetRole = role;
    if (k === this.targetKey) {
      // Mismo lugar (por ejemplo think y edit en el pizarrón): solo cambia la animación
      if (this.arrived) this.arrive();
      return;
    }
    this.targetKey = k;
    this.arrived = false;
    this.route = null;
    this.wait = 0;
  }

  repath() {
    const goal = this.world.place(this.targetKey).tile;
    const g = this.world.grid;
    this.route = g.path(this.tile, goal, this.world.blockedTiles(this)) || g.path(this.tile, goal) || [];
  }

  move(dt) {
    const g = this.world.grid;
    let rem = dt * (this.speed ?? this.config.walk_speed);
    while (rem > 0) {
      if (!this.step) {
        if (this.arrived) return;
        if (this.route === null) this.repath();
        if (!this.route.length) {
          this.arrive();
          return;
        }
        const nxt = this.route[0];
        if (this.world.blockedTiles(this).has(key(...nxt)) && this.blockedFor < 3) {
          // Casilla ocupada: espera un poco y busca otro camino; a los 3 s pasa igual (nunca se traban)
          this.wait += dt;
          this.blockedFor += dt;
          if (this.wait > 0.6) {
            this.route = null;
            this.wait = 0;
          }
          return;
        }
        this.wait = 0;
        this.blockedFor = 0;
        this.route.shift();
        const place = this.world.place(this.targetKey);
        const last = !this.route.length && key(...nxt) === key(...place.tile);
        this.facing = g.facingOf(nxt[0] - this.tile[0], nxt[1] - this.tile[1]);
        this.step = { from: [...this.foot], fromTile: [...this.tile], to: nxt,
                      toFoot: last ? place.foot : g.center(...nxt), p: 0 };
      }
      const s = this.step;
      if (rem >= 1 - s.p) {
        rem -= 1 - s.p;
        this.tile = s.to;
        this.foot = [...s.toFoot];
        this.step = null;
      } else {
        s.p += rem;
        rem = 0;
        this.foot = [0, 1].map((i) => Math.round(s.from[i] + (s.toFoot[i] - s.from[i]) * s.p));
      }
    }
  }

  arrive() {
    const p = this.world.place(this.targetKey);
    this.arrived = true;
    this.arrivedAt = this.world.now;
    this.route = [];
    this.tile = [...p.tile];
    this.foot = [...p.foot];
    if (p.facing) this.facing = p.facing;
    if (this.world.claims.get(this.targetKey) === this) this.world.claims.delete(this.targetKey);
    if (this.leaving) {
      this.setAnim(this.standAnim(false));
      // Por la puerta (cerró su programa): se despide antes de desaparecer
      if (this.leaving === "door") this.greet = "leave";
      else this.fadeDir = -1;
      return;
    }
    if (this.script) {
      this.setAnim(this.standAnim(false));
      return;
    }
    this.state = this.targetRole ? ROLE_STATE[this.targetRole] ?? "WORKING" : "IDLE";
    // En una casilla suelta (esperando al lado de un lugar ocupado) no hace la animación del rol
    const roleAnim = this.targetKey.startsWith("@") || this.displaced ? null : this.world.b.roles[this.targetRole]?.anim;
    const seated = this.world.isSeat(this.targetKey);
    this.setAnim(roleAnim && this.anims[roleAnim] ? roleAnim : this.standAnim(seated));
  }

  /** Animación quieta según la vista: sit / idle de 3/4 de frente, o la vista de referencia. */
  standAnim(seated) {
    const view = this.world.grid.facings[this.facing].view;
    if (view === "three_quarter") {
      if (seated && this.anims.sit) return "sit";
      if (this.anims.idle) return "idle";
    }
    return `ref_${view}`;
  }

  setAnim(name) {
    if (!this.anims[name]) name = this.standAnim(false);
    if (name !== this.anim) {
      this.anim = name;
      this.animT = 0;
    }
  }

  setCostume(name) {
    const id = name && this.config.costumes?.[this.id]?.[name];
    const data = id && this.world.b.characters[id];
    this.costume = data ? name : null;
    this.img = data ? data.img : this.base.img;
    this.anims = data ? data.anims : this.base.anims;
    if (data && !data.ghost) data.ghost = ghostAtlas(data.img);
    if (data?.anims.ring_on && !data.anims.ring_off) {
      // ring_off es ring_on al revés; el Anillo brilla en el píxel dorado más alto del último cuadro
      const on = data.anims.ring_on;
      data.anims.ring_off = { ...on, frames: [...on.frames].reverse() };
      data.ringPoint = ringPoint(data.img, on);
    }
    this.ringPoint = data?.ringPoint ?? null;
    this.ghost = data ? data.ghost : null;
    this.anim = null;
    this.setAnim(this.standAnim(false));
  }

  // --- guiones ---

  /** interruptible: un evento lo corta (paseo, Flash); las discusiones terminan solas. */
  startScript(gen, interruptible = true, onAbort = null) {
    this.script = { gen, interruptible, onAbort };
    this.cmd = null;
    this.abort = false;
    this.state = "SCRIPTED";
    this.leaving = null;
    this.graceUntil = null;
  }

  endScript() {
    this.script = null;
    this.cmd = null;
    this.abort = false;
    this.speed = null;
    this.walkAnims = WALK;
    this.trailOn = false;
    this.vis = 1;
    if (this.world.special === this) {
      this.world.special = null;
      this.world.specialEnd = this.world.now;   // arranca el respiro hasta la próxima (special_gap)
      this.world.tint = 0;
    }
    this.targetRole = null;          // vuelve al lugar de su rol
    this.state = this.present ? "IDLE" : "ABSENT";
    if (this.arrived) this.arrivedAt = this.world.now;
    if (this.present && this.alpha < 1) this.fadeDir = 1;   // cortado mientras no se lo veía
    if (this.leaveAfterScript && this.present) {
      const mode = this.leaveAfterScript;
      this.leaveAfterScript = null;
      this.leave(mode);
    }
  }

  runScript(dt) {
    const now = this.world.now;
    if (this.abort && this.cmd) {
      // Cortar: una caminata termina en la casilla del paso en curso; lo demás se corta ya
      if (this.cmd.kind === "walk" && !this.cmd.cut) {
        this.cmd.cut = true;
        this.route = [];
        const t = this.step ? this.step.to : this.tile;
        this.targetKey = `@${t[0]},${t[1]}`;
        if (!this.step) this.arrive();
      } else if (this.cmd.kind !== "walk") this.cmd = null;
    }
    for (let guard = 0; guard < 20; guard++) {
      if (!this.cmd) {
        if (this.abort) {
          // Punto seguro: si el guion tiene final propio (Flash vuelve a la puerta), lo hace
          const after = this.script.onAbort;
          this.abort = false;
          if (after) {
            this.script = { gen: after(this), interruptible: false, onAbort: null };
          } else return this.endScript();
        }
        const n = this.script.gen.next();
        if (n.done) return this.endScript();
        this.cmd = { ...n.value, t: 0, started: false };
      }
      const c = this.cmd;
      const first = !c.started;
      c.started = true;
      c.t += first ? 0 : dt;
      let done = false;
      switch (c.kind) {
        case "walk":
          if (first) {
            this.speed = c.speed ?? null;
            this.walkAnims = c.anims ?? WALK;
            this.goTo(c.to, null);
            if (this.cmd !== c) continue;   // goTo arrancó otro guion (no debería pasar en un guion)
          }
          this.move(dt);
          if (this.step) this.setAnim(this.walkAnims[this.world.grid.facings[this.facing].view]);
          done = this.arrived;
          if (done) {
            this.speed = null;
            this.walkAnims = WALK;
          }
          break;
        case "play":
          if (first) this.setAnim(c.anim ?? this.standAnim(false));
          done = c.t >= c.seconds;
          break;
        case "fade":
          if (first) c.from = this.alpha;
          this.alpha = c.seconds ? c.from + (c.to - c.from) * Math.min(1, c.t / c.seconds) : c.to;
          done = c.t >= c.seconds;
          break;
        case "wait":
          done = c.t >= c.seconds;
          break;
        case "face":
          this.facing = c.facing;
          this.setAnim(this.standAnim(false));
          done = true;
          break;
        case "swap":
          this.setCostume(c.costume);
          done = true;
          break;
        case "trail":
          this.trailOn = c.on;
          if (!c.on) this.trail = [];
          done = true;
          break;
        case "say":
          this.say = { text: c.text, until: now + c.seconds };
          done = true;
          break;
        case "until":
          done = c.cond() || c.t >= (c.timeout ?? 10);
          break;
        case "call":
          c.fn();
          done = true;
          break;
        case "dither":
          if (first) {
            c.from = this.vis;
            if (c.sparks) this.world.fx.push({ kind: "sparks", t0: now, x: this.foot[0], y: this.foot[1], seed: Math.floor(Math.random() * 1e9) });
          }
          this.vis = c.seconds ? c.from + (c.to - c.from) * Math.min(1, c.t / c.seconds) : c.to;
          if (c.tint) this.world.tint = 1 - this.vis;
          done = c.t >= c.seconds;
          break;
        case "jump":
          this.tile = [...c.tile];
          this.foot = [...this.world.grid.center(...c.tile)];
          this.facing = c.facing;
          this.targetKey = `@${c.tile[0]},${c.tile[1]}`;
          this.arrived = true;
          this.setAnim(this.standAnim(false));
          done = true;
          break;
        case "glint":
          if (this.ringPoint) {
            const [rx, ry] = this.ringPoint;
            const flip = this.world.grid.facings[this.facing].flip;
            this.world.fx.push({ kind: "glint", t0: now, x: this.foot[0] + (flip ? -rx : rx), y: this.foot[1] + ry });
          }
          done = true;
          break;
        default:
          done = true;
      }
      if (!done) return;
      this.cmd = null;
      if (!first && c.kind !== "walk") return;   // un comando con duración por cuadro
    }
  }

  // --- cada cuadro ---

  update(dt) {
    if (!this.present) return;
    const now = this.world.now;
    const cfg = this.config;
    this.animT += dt;
    if (this.say && now >= this.say.until) this.say = null;
    if (this.script) {
      this.runScript(dt);
      this.sampleTrail();
      return;
    }
    if (this.fadeDir) {
      this.alpha += (this.fadeDir * dt) / cfg.fade;
      if (this.alpha >= 1) {
        this.alpha = 1;
        this.fadeDir = 0;
      } else if (this.alpha <= 0) {
        this.vanish();
        return;
      }
      if (this.fadeDir > 0) return;   // termina de aparecer antes de caminar
    }
    if (this.fadeDir < 0) return;
    if (this.greet) this.greeting(now);
    if (this.waveUntil) {
      if (now < this.waveUntil) return;   // saluda quieto
      this.waveUntil = 0;
      if (this.leaving) {
        this.fadeDir = -1;
        return;
      }
      this.setAnim(this.standAnim(false));
    }

    if (this.graceUntil !== null && now >= this.graceUntil) {
      this.graceUntil = null;
      if (this.role !== "rest") this.role = "think";
    }
    // Sin eventos: en reposo se va a los leave_after s; trabajando, a 4 veces eso (una sesión que se colgó).
    // Con leave_after 0 se queda: se va solo con session_end (el servidor lo manda al cerrarse su programa)
    const quiet = now - this.lastEvent;
    if (!this.leaving && cfg.leave_after > 0 && quiet > cfg.leave_after * (this.role === "rest" ? 1 : 4)) this.leave("home");

    // Lo echaron de un lugar compartido: cuando el otro ya no lo tiene (ni reclamado ni yendo), vuelve a su rol
    if (this.displaced && !this.leaving) {
      const { place, by } = this.displaced;
      if (this.world.claims.get(place) !== by && !(by.present && by.targetKey === place)) {
        this.displaced = null;
        this.targetRole = null;
      }
    }
    // Antirebote: no cambia de lugar hasta llevar min_dwell en el actual
    if (!this.leaving && this.wantRole() !== this.targetRole) {
      if (!this.arrived || this.state === "ENTERING" || now - this.arrivedAt >= cfg.min_dwell) {
        this.goTo(this.wantRole(), this.wantRole());
        if (this.script) return;
      }
    }
    // Iba a un lugar que reclamó el dueño: busca otro
    if (!this.arrived && this.world.claims.has(this.targetKey) && this.world.claims.get(this.targetKey) !== this) {
      this.targetRole = null;
    }
    this.move(dt);
    if (this.step) this.setAnim(this.walkAnims[this.world.grid.facings[this.facing].view]);
    else if (this.leaving) return;
    // Uso alto: ya en el sillón, se tapa y teclea hasta que baje el esfuerzo o termine el turno
    else if (this.highEffort() && this.arrived && this.targetRole === "rest") this.startBlanket(() => this.highEffort() && !this.leaving);
    else this.idleScenes(now);
  }

  /**
   * Claude en uso alto (config.scenes.blanket.high: el esfuerzo del turno, que manda el hook) y trabajando:
   * en vez de ir al lugar de su rol trabaja en el sillón con la manta (BIG_BANG.md §6).
   */
  highEffort() {
    const cfg = this.config.scenes.blanket;
    return !!cfg?.who.includes(this.id) && !!this.anims.blanket_type && (cfg.high || []).includes(this.effort)
      && this.role !== "rest";
  }

  /** Rol al que va: el del último evento, salvo en uso alto (al sillón, como en reposo). */
  wantRole() {
    return this.highEffort() ? "rest" : this.role;
  }

  /** En reposo un rato: escena especial de su disfraz (Flash, Frodo) o paseo, con sorteo cada 10 s. */
  idleScenes(now) {
    if (this.state !== "IDLE" || this.role !== "rest" || !this.arrived || now < this.nextCheck) return;
    this.nextCheck = now + 10;
    const sc = this.config.scenes;
    const resting = now - this.arrivedAt;
    const gapOk = now >= this.world.specialEnd + (sc.special_gap ?? 0);   // respiro entre especiales
    for (const name of Object.keys(this.config.costumes?.[this.id] || {})) {
      const cfg = sc[name];
      if (!SPECIALS[name] || !cfg || this.world.special || !gapOk || resting <= cfg.after) continue;
      if (now >= (this.cooldowns[name] ?? 0) && Math.random() < cfg.chance) return this.startSpecial(name);
    }
    const wii = sc.wii;
    if (wii && resting > wii.after && now >= (this.cooldowns.wii ?? 0) && Math.random() < wii.chance && this.startWii()) return;
    const bl = sc.blanket;
    if (bl && resting > bl.after && now >= (this.cooldowns.blanket ?? 0) && Math.random() < bl.chance && this.startBlanket()) return;
    if (resting > sc.wander.after && Math.random() < sc.wander.chance) {
      this.startScript(wander(this));
      this.script.kind = "wander";   // en el paseo se puede charlar al cruzarse (chatter.js)
    }
  }

  /** Jugar a la Wii (scenes.wii): solo quien tenga la animación y con la tele libre. Un evento lo corta. */
  startWii() {
    const cfg = this.config.scenes.wii;
    if (!this.present || this.script || !this.anims.wii || !cfg?.who.includes(this.id)) return false;
    if (this.world.occupant(cfg.place, this)) return false;
    this.cooldowns.wii = this.world.now + cfg.cooldown;
    this.startScript(playWii(this));
    return true;
  }

  /**
   * Manta y notebook (scenes.blanket): solo quien tenga las animaciones y ya sentado en el sillón (se anima
   * en su asiento, sin caminar). hold: ver scenes.blanket; con hold los eventos no lo cortan (lo termina
   * hold), sin hold sí: cierra la notebook y se la saca. Cerrar la sesión lo corta siempre.
   */
  startBlanket(hold = null) {
    const cfg = this.config.scenes.blanket;
    if (!this.present || this.script || !this.arrived || !this.anims.blanket_type || !cfg?.who.includes(this.id)) return false;
    if (!this.world.b.seats.couch?.includes(this.targetKey)) return false;
    if (!hold) this.cooldowns.blanket = this.world.now + cfg.cooldown;
    this.startScript(blanket(this, Math.random, hold), !hold, blanketOff);
    return true;
  }

  /** Arranca la escena especial de un disfraz (flash, hobbit); una sola a la vez en todo el living.
   *  El respiro special_gap se chequea en idleScenes: las teclas de debug (main.js) lo saltean. */
  startSpecial(name) {
    if (!this.present || this.script || this.world.special || !this.config.costumes?.[this.id]?.[name]) return false;
    const [script, onAbort] = SPECIALS[name];
    this.world.special = this;
    this.cooldowns[name] = this.world.now + this.config.scenes[name].cooldown;
    this.startScript(script(this), true, onAbort);
    return true;
  }

  sampleTrail() {
    if (!this.trailOn) return;
    const a = this.anims[this.anim];
    if (!a) return;
    const n = a.frames.length;
    const i = a.loop ? Math.floor(this.animT * a.fps) % n : Math.min(n - 1, Math.floor(this.animT * a.fps));
    this.trail.unshift({ anim: a, i, foot: [...this.foot], flip: this.world.grid.facings[this.facing].flip,
                         tile: this.drawTile() });
    this.trail.length = Math.min(this.trail.length, TRAIL + 1);
  }

  vanish() {
    this.alpha = 0;
    this.fadeDir = 0;
    this.present = false;
    this.state = "ABSENT";
    this.exit = this.leaving === "door" ? this.outside : this.home;
    this.leaving = null;
    this.targetKey = null;
    this.aside = null;
    this.step = null;
    this.say = null;
    this.greet = null;
    this.waveUntil = 0;
    this.world.release(this);
  }

  /** Primera carga con el servidor: ya estaba trabajando, aparece directo en el lugar de su rol (sin entrar). */
  placeNow() {
    if (!this.present || this.script || this.leaving) return;
    this.alpha = 1;
    this.fadeDir = 0;
    this.greet = null;   // ya estaba: no saluda
    this.waveUntil = 0;
    this.goTo(this.wantRole(), this.wantRole());
    if (this.script) return;
    this.step = null;
    if (!this.arrived) this.arrive();
    this.arrivedAt = this.world.now - this.config.min_dwell;   // puede cambiar de lugar con el próximo evento
  }

  /** Después de una pausa larga (Lively pausado): salta al final de lo que estaba haciendo. */
  snap() {
    if (!this.present) return;
    if (this.script) {
      // Termina el guion de golpe: sin disfraz, en el lugar de su rol
      if (this.costume) this.setCostume(null);
      this.blanketOn = false;
      this.step = null;
      this.world.fx = [];
      this.endScript();
      this.alpha = 1;
      this.goTo(this.wantRole(), this.wantRole());
    }
    if (this.leaving) return this.vanish();
    this.alpha = 1;
    this.fadeDir = 0;
    this.greet = null;
    this.waveUntil = 0;
    if (!this.arrived && this.targetKey) {
      this.step = null;
      this.arrive();
    }
  }

  // --- dibujo ---

  drawTile() {
    // Para tapar, durante un paso cuenta la casilla más cerca de la cámara de las dos
    return this.step ? [Math.max(this.step.fromTile[0], this.step.to[0]), Math.max(this.step.fromTile[1], this.step.to[1])]
                     : this.tile;
  }

  /** El personaje y, si corre con estela, sus clones (más viejos, más transparentes). */
  actors() {
    if (!this.present || this.alpha <= 0 || this.vis <= 0) {
      this.box = null;
      return [];
    }
    const f = this.world.grid.facings[this.facing];
    const a = this.anims[this.anim] || this.anims[`ref_${f.view}`];
    const n = a.frames.length;
    let i = Math.floor(this.animT * a.fps);
    i = a.loop ? i % n : Math.min(n - 1, i);
    const foot = [this.foot[0], this.foot[1] - this.lift()];
    const main = spriteActor(this.img, a, i, foot, this.drawTile(), f.flip, this.alpha, this.vis);
    this.box = main.box;
    const out = [main];
    if (this.ghost) {
      for (let k = 1; k < this.trail.length; k++) {
        const s = this.trail[k];
        if (s.foot[0] === this.foot[0] && s.foot[1] === this.foot[1]) continue;
        out.push(spriteActor(this.ghost, s.anim, s.i, s.foot, s.tile, s.flip, 0.55 * (1 - k / (TRAIL + 1)) * this.alpha));
      }
    }
    return out;
  }

  /**
   * Las animaciones bajadas para el escritorio (type, animations.*.lower) se suben a su altura fuera de
   * él: Penny con el celular en la banqueta de la cocina.
   */
  lift() {
    const cfg = this.world.b.animations?.[this.anim];
    if (!cfg?.lower || !this.arrived || this.world.b.seats.desk?.includes(this.targetKey)) return 0;
    return cfg.lower_by_character?.[this.id] ?? cfg.lower;
  }

  /** Lo que necesitan los efectos: en qué lugar está trabajando y desde cuándo, o null. */
  effectState() {
    if (!this.present || !this.arrived || this.leaving || this.script || !this.targetRole || !this.targetKey || this.displaced) return null;
    return { place: this.targetKey, role: this.targetRole, since: this.arrivedAt };
  }
}

/** Píxel dorado más alto de la mitad de arriba del último cuadro, relativo a los pies (frodo_preview.ring_point). */
function ringPoint(img, anim) {
  const [sx, sy, w, h] = anim.frames[anim.frames.length - 1];
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const g = c.getContext("2d");
  g.drawImage(img, sx, sy, w, h, 0, 0, w, h);
  const d = g.getImageData(0, 0, w, Math.floor(h / 2)).data;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] > 0 && d[i] > 200 && d[i + 1] > 150 && d[i + 2] < 140) {
      const p = i / 4;
      return [(p % w) - anim.anchor[0], Math.floor(p / w) - anim.anchor[1]];
    }
  }
  return [20, -70];
}
