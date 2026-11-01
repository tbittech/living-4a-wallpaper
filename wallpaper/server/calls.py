"""Requests de OmniRoute -> eventos normalizados (CONEXION.md §2) para Leonard y Penny.

OmniRoute deja cada request en ~/.omniroute/call_logs/<fecha>/<hora>_<id>.json, recién cuando terminó
(`summary`: método, path, status, duración; `requestBody` a veces recortado). De cada archivo nuevo sale un evento:

- quién: por el path (config.json -> omniroute.clients): /v1/responses es Codex (Leonard), :generateContent es
  Gemini (Penny). Lo demás (/v1/messages es Claude Code pasando por OmniRoute, ya lo siguen los hooks; /api/...
  es el panel) se ignora.
- qué: si lo último del input es la salida de una herramienta, la herramienta que se acaba de correr (tool_call);
  si no, un mensaje nuevo del usuario (request_start). Status >= 400 -> error.

Codex en "code mode" corre todo con `exec` (JS): adentro se busca la primera `tools.<nombre>(` para saber si fue
exec_command, apply_patch, web_search o un mcp__. Solo viaja ese nombre, nunca el código ni el texto.
"""

import json
import re

from state import TOOL_RE

INNER_TOOL_RE = re.compile(r"\btools\.([A-Za-z0-9_]{1,64})\s*\(")
DEFAULT_CLIENTS = {"/v1/responses": "codex", ":generateContent": "gemini", ":streamGenerateContent": "gemini"}


def client_of(summary, clients=None):
    path = str(summary.get("path") or "")
    for frag, source in (clients or DEFAULT_CLIENTS).items():
        if not frag.startswith("_") and source and frag in path:
            return source
    return None


def _tool_name(name, payload):
    """Nombre de la herramienta; para el `exec` de Codex, la de adentro."""
    if name == "exec" and isinstance(payload, str):
        m = INNER_TOOL_RE.search(payload)
        if m:
            return m.group(1)
    return name


def last_tool(body):
    """Herramienta cuya salida cierra el input (lo que la IA acaba de correr), o None si cierra un mensaje."""
    if not isinstance(body, dict):
        return None
    items = body.get("input")
    if isinstance(items, list) and items:          # OpenAI Responses (Codex)
        last = items[-1] if isinstance(items[-1], dict) else {}
        if not str(last.get("type", "")).endswith("_output"):
            return None
        call_id = last.get("call_id")
        for it in reversed(items[:-1]):
            if not isinstance(it, dict) or not str(it.get("type", "")).endswith("_call"):
                continue
            if call_id is None or it.get("call_id") == call_id:
                return _tool_name(it.get("name"), it.get("input") or it.get("arguments"))
        return None
    messages = body.get("messages")
    if isinstance(messages, list) and messages:    # OpenAI Chat (así guarda OmniRoute lo de Gemini CLI)
        last = messages[-1] if isinstance(messages[-1], dict) else {}
        if last.get("role") != "tool":
            return None
        if isinstance(last.get("name"), str):
            return last["name"]
        for m in reversed(messages[:-1]):
            for tc in (m.get("tool_calls") or []) if isinstance(m, dict) else []:
                if isinstance(tc, dict) and tc.get("id") == last.get("tool_call_id"):
                    return (tc.get("function") or {}).get("name")
        return None
    contents = body.get("contents")
    if isinstance(contents, list) and contents:    # Gemini: la última parte es un functionResponse
        parts = contents[-1].get("parts") if isinstance(contents[-1], dict) else None
        for p in parts or []:
            if isinstance(p, dict) and isinstance(p.get("functionResponse"), dict):
                return p["functionResponse"].get("name")
    return None


def event_of(data, clients=None):
    """Evento (sin normalizar) para un call_log ya leído, o None si no es de una IA que se sigue."""
    summary = data.get("summary") if isinstance(data, dict) else None
    if not isinstance(summary, dict):
        return None
    source = client_of(summary, clients)
    if source is None:
        return None
    ev = {"source": source, "session": "omniroute"}
    provider = summary.get("provider")
    if isinstance(provider, str):
        ev["provider"] = provider.lower()
    status = summary.get("status")
    if isinstance(status, int) and status >= 400:
        ev.update(type="error", status=status)
        return ev
    tool = last_tool(data.get("requestBody"))
    if isinstance(tool, str) and TOOL_RE.match(tool):
        ev.update(type="tool_call", tool=tool)
    else:
        ev["type"] = "request_start"
    return ev


def read_log(path):
    """El JSON del call_log, o None si todavía se está escribiendo (o no es JSON)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
