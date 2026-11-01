"""Estado grueso por source (claude, codex, gemini) para el snapshot del WebSocket.

Solo lo necesario para que el frontend, al conectarse o reconectarse, sepa quién está y qué está haciendo:
presente o no, sesiones abiertas, estado (idle / thinking / working), rol, herramienta y desde cuándo.
También valida los eventos que llegan: lo que no está en la lista se descarta (nunca viaja texto libre).
"""

import json
import re
import time
from pathlib import Path

TYPES = {
    "session_start", "request_start", "tool_call", "tool_result", "turn_end", "session_end",
    "error", "fallback", "gateway_up", "gateway_down",
}
SOURCE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
SESSION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
TOOL_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")   # mcp__servidor__herramienta entra
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
PROVIDER_RE = re.compile(r"^[a-z0-9_.-]{1,32}$")
MAX_FILES = 8
DAY_MS = 24 * 3600 * 1000
# Una sesión que no manda nada en este tiempo se da por cerrada (Claude Code cerrado de golpe, sin SessionEnd)
SESSION_TTL_MS = 12 * 3600 * 1000


def now_ms():
    return int(time.time() * 1000)


def normalize(raw):
    """Evento normalizado (CONEXION.md §2) o None si no vale. Solo pasan los campos conocidos y con forma de id."""
    if not isinstance(raw, dict):
        return None
    source, typ = raw.get("source"), raw.get("type")
    if not isinstance(source, str) or not SOURCE_RE.match(source) or typ not in TYPES:
        return None
    ts = raw.get("ts")
    if ts is None:
        ts = now_ms()
    elif isinstance(ts, bool) or not isinstance(ts, (int, float)):
        return None
    ts = int(ts)
    if abs(ts - now_ms()) > DAY_MS:   # reloj roto o ts en segundos: vale la hora del servidor
        ts = now_ms()
    ev = {"source": source, "type": typ, "ts": ts}
    session = raw.get("session")
    ev["session"] = session if isinstance(session, str) and SESSION_RE.match(session) else source
    tool = raw.get("tool")
    if typ in ("tool_call", "tool_result") and isinstance(tool, str) and TOOL_RE.match(tool):
        ev["tool"] = tool
    files = raw.get("files")
    if isinstance(files, list):
        ok = [f for f in files[:MAX_FILES]
              if isinstance(f, str) and 0 < len(f) <= 260 and not any(c in f for c in "\r\n\t\0")]
        if ok:
            ev["files"] = ok
    status = raw.get("status")
    if isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599:
        ev["status"] = status
    provider = raw.get("provider")
    if isinstance(provider, str) and PROVIDER_RE.match(provider):
        ev["provider"] = provider
    if raw.get("effort") in EFFORTS:
        ev["effort"] = raw["effort"]
    return ev


def tool_role(tool, tool_roles):
    """Igual que toolRole de character.js: mcp__* va a web, lo desconocido a edit."""
    t = (tool or "").lower()
    if t.startswith("mcp__"):
        return "web"
    return tool_roles.get(t, "edit")


class State:
    def __init__(self, tool_roles=None):
        self.tool_roles = {k: v for k, v in (tool_roles or {}).items() if not k.startswith("_")}
        self.agents = {}     # source -> dict (ver _agent)
        self.gateway = None  # OmniRoute: True / False / None (no se sabe)

    def _agent(self, source):
        return self.agents.setdefault(source, {
            "present": False, "sessions": {}, "state": "idle", "role": "rest", "tool": None,
            "since": 0, "last_ts": 0, "effort": None,
        })

    def _set(self, a, state, role, tool, ts):
        if (a["state"], a["role"], a["tool"]) != (state, role, tool):
            a["since"] = ts
        a["state"], a["role"], a["tool"] = state, role, tool

    def apply(self, ev):
        """Actualiza el estado con un evento ya normalizado. Devuelve True si hay que reenviarlo al frontend."""
        typ, ts = ev["type"], ev["ts"]
        if typ in ("gateway_up", "gateway_down"):
            self.gateway = typ == "gateway_up"
            return True
        a = self._agent(ev["source"])
        a["last_ts"] = max(a["last_ts"], ts)
        if typ == "session_end":
            a["sessions"].pop(ev["session"], None)
            if a["sessions"]:
                return False   # quedan otras sesiones de la misma IA: el personaje se queda
            a["present"] = False
            self._set(a, "idle", "rest", None, ts)
            return True
        was = a["present"]
        a["sessions"][ev["session"]] = ts
        a["present"] = True
        if "effort" in ev:
            a["effort"] = ev["effort"]
        if typ == "session_start":
            if not was:
                self._set(a, "idle", "rest", None, ts)
        elif typ == "request_start":
            self._set(a, "thinking", "think", None, ts)
        elif typ == "tool_call":
            self._set(a, "working", tool_role(ev.get("tool"), self.tool_roles), ev.get("tool"), ts)
        elif typ == "tool_result":
            self._set(a, "thinking", "think", None, ts)
        elif typ == "turn_end":
            self._set(a, "idle", "rest", None, ts)
        return True

    def prune(self, now=None):
        """Olvida las sesiones que hace mucho que no mandan nada. Devuelve True si cambió algo."""
        now = now or now_ms()
        changed = False
        for a in self.agents.values():
            for sid, ts in list(a["sessions"].items()):
                if now - ts > SESSION_TTL_MS:
                    del a["sessions"][sid]
                    changed = True
            if a["present"] and not a["sessions"]:
                a["present"] = False
                self._set(a, "idle", "rest", None, now)
                changed = True
        return changed

    def snapshot(self):
        agents = {s: {"present": a["present"], "sessions": len(a["sessions"]), "state": a["state"],
                      "role": a["role"], "tool": a["tool"], "since": a["since"], "last_ts": a["last_ts"],
                      "effort": a.get("effort")}
                  for s, a in self.agents.items()}
        return {"type": "snapshot", "server_ts": now_ms(), "agents": agents, "gateway": self.gateway}

    # --- persistencia: si se reinicia el servidor, la sesión de Claude sigue abierta y Sheldon no se tiene que ir ---

    def save(self, path):
        path = Path(path)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"agents": self.agents, "gateway": self.gateway}), encoding="utf-8")
        tmp.replace(path)

    def load(self, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for source, a in (data.get("agents") or {}).items():
            if not isinstance(a, dict) or not SOURCE_RE.match(source):
                continue
            b = self._agent(source)
            for k in b:
                if k in a:
                    b[k] = a[k]
            if not isinstance(b["sessions"], dict):
                b["sessions"] = {}
        self.prune()   # gateway no se carga: OmniRoute avisa de nuevo si sigue prendido
