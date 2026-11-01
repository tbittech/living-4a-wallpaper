"""Hook de Claude Code para el wallpaper: stdin (JSON del hook) -> evento normalizado -> POST /event.

Se configura el mismo comando para los seis hooks (ver settings_snippet.json); el evento sale de hook_event_name:

    SessionStart -> session_start (salvo source "compact": es la misma sesión)
    UserPromptSubmit -> request_start      PreToolUse -> tool_call {tool}      PostToolUse -> tool_result {tool}
    Stop -> turn_end                       SessionEnd -> session_end

Solo viajan source, session (el id de Claude Code), type, tool (el nombre), effort y ts. Nunca el prompt, el
comando, el contenido, las rutas ni la respuesta de la herramienta.
effort: el nivel de esfuerzo del turno (low / medium / high / xhigh / max), leído del final del transcript
(campo perTurnEffort de la última respuesta). En PreToolUse y Stop ya es el del turno en curso; en
UserPromptSubmit todavía es el del turno anterior (se corrige en la primera herramienta).
No tiene que notarse: solo biblioteca estándar (corre con python -I -S: sin site, ~35 ms menos), sin salida,
siempre exit 0. Si el servidor no está (no existe server/.running.json o su proceso ya no vive) lo arranca con
pythonw, desprendido de Claude Code, y espera a que escuche (~1 s, solo la primera vez): así Sheldon aparece al
abrir Claude Code aunque Windows recién haya arrancado. Nunca se conecta a ciegas: en Windows conectarse a un puerto
cerrado no falla enseguida, espera todo el timeout. session_end no lo arranca.
WALLPAPER_PORT=8775 manda a ese puerto sin mirar .running.json (pruebas).
"""

import json
import os
import sys
import time

TYPES = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "request_start",
    "PreToolUse": "tool_call",
    "PostToolUse": "tool_result",
    "Stop": "turn_end",
    "SessionEnd": "session_end",
}
EFFORTS = ("low", "medium", "high", "xhigh", "max")
EFFORT_TAIL = 256 * 1024   # bytes del final del transcript donde buscar la última respuesta
SERVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server")
RUNNING = os.path.join(SERVER_DIR, ".running.json")
STARTING = os.path.join(SERVER_DIR, ".starting")   # marca de arranque: dos hooks seguidos no lanzan dos servidores
START_WAIT = 2.0       # segundos esperando a que el servidor recién lanzado escriba .running.json
START_RETRY = 15       # segundos antes de volver a intentar si un arranque no prosperó
CONNECT_TIMEOUT = 0.2   # en 127.0.0.1 conectar tarda menos de 1 ms si el servidor está
TIMEOUT = 0.5


def alive(pid):
    """¿Sigue vivo el proceso del servidor? (si murió de golpe, .running.json quedó viejo)."""
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            return True
        except OSError:
            return False
    import ctypes
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return bool(ok) and code.value == 259     # STILL_ACTIVE


def running():
    """Puerto del servidor si está vivo, si no None."""
    try:
        with open(RUNNING, encoding="utf-8") as f:
            run = json.load(f)
    except (OSError, ValueError):
        return None
    return run["port"] if alive(int(run["pid"])) else None


def start_server():
    """Lanza server.py con pythonw, fuera del job de Claude Code (si lo cierran, el servidor sigue)."""
    try:
        if time.time() - os.path.getmtime(STARTING) < START_RETRY:
            return False   # otro hook ya lo está arrancando
    except OSError:
        pass
    with open(STARTING, "w") as f:
        f.write(str(os.getpid()))
    import subprocess
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    cmd = [exe, os.path.join(SERVER_DIR, "server.py"), "--quiet"]
    base = 0x00000008 | 0x00000200 | 0x08000000   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    for flags in (base | 0x01000000, base):       # + CREATE_BREAKAWAY_FROM_JOB, si el job lo permite
        try:
            subprocess.Popen(cmd, creationflags=flags, close_fds=True, cwd=SERVER_DIR,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            continue
    return False


def effort(payload):
    """Esfuerzo del turno: el último "perTurnEffort" del final del transcript, o None."""
    path = payload.get("transcript_path")
    if not isinstance(path, str) or not path:
        return None
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - EFFORT_TAIL))
        tail = f.read()
    i = tail.rfind(b'"perTurnEffort":"')
    if i < 0:
        return None
    start = i + len(b'"perTurnEffort":"')
    value = tail[start:tail.find(b'"', start)].decode("ascii", "replace")
    return value if value in EFFORTS else None


def event(payload):
    typ = TYPES.get(payload.get("hook_event_name"))
    if typ is None:
        return None
    if typ == "session_start" and payload.get("source") == "compact":
        return None
    ev = {"source": "claude", "type": typ, "ts": int(time.time() * 1000)}
    session = payload.get("session_id")
    if isinstance(session, str) and session:
        ev["session"] = session[:64]
    tool = payload.get("tool_name")
    if typ in ("tool_call", "tool_result") and isinstance(tool, str) and tool:
        ev["tool"] = tool[:64]
    if typ in ("request_start", "tool_call", "turn_end"):
        try:
            e = effort(payload)
        except OSError:
            e = None
        if e:
            ev["effort"] = e
    return ev


def main():
    ev = event(json.loads(sys.stdin.buffer.read() or b"{}"))
    if ev is None:
        return
    port = os.environ.get("WALLPAPER_PORT") or running()
    tries = 1
    if not port:
        if ev["type"] == "session_end" or os.name != "nt" or not start_server():
            return
        end = time.time() + START_WAIT
        while not port and time.time() < end:
            time.sleep(0.1)
            port = running()
        if not port:
            return
        tries = 5   # .running.json se escribe un instante antes de que el puerto escuche
    # HTTP a mano: http.client importa email.* y tarda más que todo el resto del hook
    import socket
    body = json.dumps(ev).encode()
    head = (f"POST /event HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode()
    for i in range(tries):
        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=CONNECT_TIMEOUT) as s:
                s.settimeout(TIMEOUT)
                s.sendall(head + body)
                s.recv(64)   # espera la respuesta: así el PostToolUse nunca llega antes que su PreToolUse
            return
        except OSError:
            if i + 1 == tries:
                raise
            time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except BaseException:   # nunca molestar a Claude Code: ni errores, ni salida, ni código distinto de 0
        pass
    sys.exit(0)
