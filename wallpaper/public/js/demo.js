// Simulador de eventos (?demo=1): sesiones verosímiles por IA, sin servidor ni IAs reales.
// Los eventos tienen el formato normalizado de CONEXION.md §2 y entran por la misma cola que los reales.

const TOOLS = [["Bash", 4], ["Edit", 3], ["Read", 4], ["Grep", 2], ["Write", 1], ["WebFetch", 1], ["WebSearch", 1]];

const rand = (a, b) => a + Math.random() * (b - a);

function pickTool() {
  let r = Math.random() * TOOLS.reduce((s, [, w]) => s + w, 0);
  for (const [name, w] of TOOLS) if ((r -= w) < 0) return name;
  return TOOLS[0][0];
}

export class Demo {
  /** emit(evento); sources: IAs a simular; leaveAfter: para que a veces la pausa alcance para irse. */
  constructor(emit, sources, leaveAfter) {
    this.emit = emit;
    this.leaveAfter = leaveAfter;
    this.auto = true;
    this.agents = sources.map((source, i) => ({ source, phase: "off", next: 1 + i * 6, tools: 0 }));
  }

  send(source, type, extra = {}) {
    this.emit({ source, session: `demo-${source}`, type, ts: Date.now(), ...extra });
  }

  update(now) {
    if (!this.auto) return;
    for (const ag of this.agents) {
      if (now < ag.next) continue;
      const s = ag.source;
      if (ag.phase === "off") {
        this.send(s, "session_start");
        ag.phase = "idle";
        ag.next = now + rand(3, 8);
      } else if (ag.phase === "idle") {
        this.send(s, "request_start");
        ag.phase = "thinking";
        ag.tools = Math.floor(rand(1, 7));
        ag.next = now + rand(1, 4);
      } else if (ag.phase === "thinking") {
        if (ag.tools > 0) {
          this.send(s, "tool_call", { tool: pickTool() });
          ag.phase = "tool";
          ag.next = now + rand(2, 9);
        } else {
          this.send(s, "turn_end");
          const r = Math.random();
          if (r < 0.1) {
            this.send(s, "session_end");
            ag.phase = "off";
            ag.next = now + rand(20, 60);
          } else {
            ag.phase = "idle";
            // A veces una pausa más larga que leave_after: el personaje se va a su pieza y vuelve
            ag.next = now + (r < 0.3 ? this.leaveAfter + rand(5, 20) : rand(8, 30));
          }
        }
      } else if (ag.phase === "tool") {
        this.send(s, "tool_result");
        ag.tools--;
        ag.phase = "thinking";
        ag.next = now + rand(0.5, 2.5);
      }
    }
  }
}

/** Teclas de prueba: mandan eventos a la IA elegida. Devuelve el texto de ayuda. */
export function bindKeys(demo, getSource, setSource, sources, toggles) {
  const tools = { 1: "Bash", 2: "Edit", 3: "Read", 4: "WebFetch" };
  const pick = { s: "claude", l: "codex", p: "gemini" };
  addEventListener("keydown", (e) => {
    const k = e.key.toLowerCase();
    const src = getSource();
    if (tools[k]) demo.send(src, "tool_call", { tool: tools[k] });
    else if (k === "r") demo.send(src, "request_start");
    else if (k === "t") demo.send(src, "turn_end");
    else if (k === "n") demo.send(src, "session_start");
    else if (k === "x") demo.send(src, "session_end");
    else if (k === "a") demo.auto = !demo.auto;
    else if (pick[k] && sources.includes(pick[k])) setSource(pick[k]);
    else if (toggles[k]) toggles[k]();
  });
  return "1 shell · 2 edit · 3 read · 4 web · R pensar · T fin de turno · N entrar · X salir · A auto · S/L/P personaje · F Flash · H Frodo · W pasear · G Wii · M manta · C chocala · D debug";
}
