// Conexión con el servidor (server/server.py): WebSocket con reconexión y espera creciente (0,5 -> 10 s).
//
// Al conectar llega {"type": "snapshot", server_ts, agents: {claude: {present, sessions, state, role, tool,
// since, last_ts}}} y después cada evento como {"type": "event", event: {...}} (formato de CONEXION.md §2).
// Sin servidor (por ejemplo con python -m http.server) reintenta para siempre sin molestar: el living queda vacío.

const MIN_WAIT = 0.5, MAX_WAIT = 10;

/**
 * url: ws://host/ws. onSnapshot(snapshot, first): first es la primera vez desde que cargó la página.
 * onEvent(evento). onStatus("conectado" | "reintentando en N s"). Devuelve {status, close()}.
 */
export function connect(url, { onSnapshot, onEvent, onStatus = () => {} }) {
  let wait = MIN_WAIT, first = true, ws = null, timer = null, closed = false;
  const net = {
    status: "conectando",
    close() {
      closed = true;
      clearTimeout(timer);
      ws?.close();
    },
  };
  const status = (s) => {
    net.status = s;
    onStatus(s);
  };

  function open() {
    if (closed) return;
    ws = new WebSocket(url);
    ws.onopen = () => {
      wait = MIN_WAIT;
      status("conectado");
    };
    ws.onmessage = (m) => {
      let msg;
      try {
        msg = JSON.parse(m.data);
      } catch {
        return;
      }
      if (msg.type === "snapshot") {
        onSnapshot(msg, first);
        first = false;
      } else if (msg.type === "event" && msg.event) {
        onEvent(msg.event);
      }
    };
    ws.onclose = () => {
      ws = null;
      if (closed) return;
      status(`reintentando en ${wait} s`);
      timer = setTimeout(open, wait * 1000);
      wait = Math.min(MAX_WAIT, wait * 2);
    };
    ws.onerror = () => {};   // después viene onclose
  }

  open();
  return net;
}

/** Evento sintético que deja a un personaje en el estado de un agente del snapshot. */
export function eventFor(source, agent) {
  const effort = agent.effort ? { effort: agent.effort } : {};
  if (agent.role === "rest") return { source, type: "turn_end", ...effort };
  if (agent.role === "think") return { source, type: "request_start", ...effort };
  return { source, type: "tool_call", tool: agent.tool || ROLE_TOOL[agent.role] || "Edit", ...effort };
}

const ROLE_TOOL = { shell: "Bash", edit: "Edit", read: "Read", web: "WebFetch", think: "Task" };
