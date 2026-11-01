"""Servidor del wallpaper (WALLPAPER.md §5): estáticos de public/ + eventos en vivo.

    python wallpaper/server/server.py [--port 8765] [--host 127.0.0.1]

- GET /           public/ (index.html, config.json, js/, bundle/)
- GET /ws         WebSocket: al conectar {"type": "snapshot", ...}; después {"type": "event", "event": {...}}
- POST /event     un evento normalizado (CONEXION.md §2) o una lista. Se valida y se descarta todo texto libre
- GET /state      el snapshot actual (debug)

Quién está lo deciden los procesos (procs.py, config.json -> processes): cada `every` segundos se miran Windows y
WSL; con Claude, Codex o Gemini CLI abierto su personaje tiene la sesión "proc" y se queda aunque no haga nada; al
cerrarse el programa se cierran todas sus sesiones y se va. Al arrancar se mira antes de atender: con todo cerrado
(o recién prendida la compu) el living queda vacío aunque .state.json diga otra cosa.

OmniRoute (config.json -> omniroute): cada `every` segundos se pide `url` (health sin auth), solo para gateway_up /
gateway_down. Sus call_logs nuevos (calls.py) mueven a Leonard y Penny, pero solo si su programa está abierto.

Escucha solo en 127.0.0.1. El puerto sale de --port, de WALLPAPER_PORT o es 8765.
Mientras corre deja server/.running.json con el puerto y el pid: el hook lo lee para saber a dónde mandar y,
si no está, ni intenta conectarse (en Windows conectarse a un puerto cerrado tarda lo que dure el timeout).
El estado se guarda en server/.state.json: al reiniciar el servidor la sesión de Claude sigue presente.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from aiohttp import WSMsgType, web

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from calls import event_of, read_log  # noqa: E402
from procs import running  # noqa: E402
from state import State, normalize, now_ms  # noqa: E402

PUBLIC = HERE.parent / "public"
RUNNING = HERE / ".running.json"
STATE_FILE = HERE / ".state.json"
MAX_BODY = 64 * 1024
MAX_EVENTS = 50          # por POST


def log(app, *parts):
    if not app["quiet"]:
        print(*parts, flush=True)


async def broadcast(app, msg):
    data = json.dumps(msg)
    for ws in list(app["clients"]):
        try:
            await ws.send_str(data)
        except (ConnectionError, RuntimeError):
            app["clients"].discard(ws)


def schedule_save(app):
    """Guarda el estado como mucho una vez por segundo."""
    t = app["timers"]
    if t.get("save") is None:
        t["save"] = asyncio.get_running_loop().call_later(1.0, save_now, app)


def save_now(app):
    app["timers"]["save"] = None
    try:
        app["state"].save(STATE_FILE)
    except OSError as e:
        log(app, "no se pudo guardar el estado:", e)


async def ws_handler(request):
    app = request.app
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    app["clients"].add(ws)
    log(app, f"ws: conectado ({len(app['clients'])})")
    try:
        await ws.send_str(json.dumps(app["state"].snapshot()))
        async for msg in ws:   # el frontend no manda nada; esto solo espera a que se cierre
            if msg.type == WSMsgType.ERROR:
                break
    finally:
        app["clients"].discard(ws)
        log(app, f"ws: desconectado ({len(app['clients'])})")
    return ws


async def event_handler(request):
    app = request.app
    try:
        raw = json.loads(await request.read())
    except (ValueError, UnicodeDecodeError):
        return web.json_response({"ok": False, "error": "json"}, status=400)
    items = raw if isinstance(raw, list) else [raw]
    accepted = 0
    for item in items[:MAX_EVENTS]:
        ev = normalize(item)
        if ev is None:
            continue
        accepted += 1
        if app["state"].apply(ev):
            await broadcast(app, {"type": "event", "event": ev})
        log(app, f"{ev['source']} {ev['type']}{' ' + ev['tool'] if 'tool' in ev else ''}")
    if accepted:
        schedule_save(app)
    return web.json_response({"ok": accepted > 0, "accepted": accepted}, status=200 if accepted else 400)


async def state_handler(request):
    return web.json_response(request.app["state"].snapshot())


async def index_handler(request):
    return web.FileResponse(PUBLIC / "index.html")


@web.middleware
async def no_cache(request, handler):
    # Sin caché: después de reexportar el bundle o tocar el JS, Lively recarga lo nuevo
    resp = await handler(request)
    if isinstance(resp, web.StreamResponse) and not isinstance(resp, web.WebSocketResponse):
        resp.headers.setdefault("Cache-Control", "no-cache")
    return resp


async def prune_loop(app):
    while True:
        await asyncio.sleep(600)
        if app["state"].prune():
            schedule_save(app)


async def apply_all(app, events):
    state = app["state"]
    for raw in events:
        ev = normalize(raw)
        if ev and state.apply(ev):
            await broadcast(app, {"type": "event", "event": ev})


async def check_procs(app, cfg, misses):
    """Una pasada de procs.py: abre la sesión "proc" de los que están y cierra todo de los que se fueron.
    Un programa tiene que faltar `misses` pasadas seguidas para irse (un ps de WSL que falló no lo echa)."""
    found = await asyncio.get_running_loop().run_in_executor(None, running, cfg)
    state, events, gone = app["state"], [], app["proc_missing"]
    for source in set(found) | set(state.agents):
        a = state.agents.get(source)
        if source in found:
            gone.pop(source, None)
            if a is None or "proc" not in a["sessions"]:
                events.append({"source": source, "type": "session_start", "session": "proc"})
                log(app, f"proceso: {source} abierto")
            else:
                a["sessions"]["proc"] = now_ms()   # que prune no la dé por vieja
            continue
        if not a or not a["sessions"]:
            continue
        gone[source] = gone.get(source, 0) + 1
        if gone[source] >= misses:
            for sid in list(a["sessions"]):
                events.append({"source": source, "type": "session_end", "session": sid})
            log(app, f"proceso: {source} cerrado")
    if events:
        await apply_all(app, events)
        schedule_save(app)


async def procs_loop(app, cfg):
    while True:
        await asyncio.sleep(cfg.get("every", 3))
        await check_procs(app, cfg, cfg.get("misses", 2))


async def gateway_loop(app, cfg):
    """Sigue a OmniRoute: prendido -> gateway_up, apagado -> gateway_down (quién está lo deciden los procesos)."""
    from aiohttp import ClientError, ClientSession, ClientTimeout
    url = cfg.get("url", "http://127.0.0.1:20128/api/health/ping")
    async with ClientSession(timeout=ClientTimeout(total=cfg.get("timeout", 1.5))) as http:
        while True:
            try:
                async with http.get(url) as r:
                    up = r.status < 500
            except (ClientError, asyncio.TimeoutError, OSError):
                up = False
            state = app["state"]
            # Lo que quedó de antes, cuando OmniRoute abría sesiones: ahora las abren los procesos
            stale = [{"source": s, "type": "session_end", "session": "omniroute"}
                     for s, a in state.agents.items() if "omniroute" in a["sessions"]] if app["procs"] is not None else []
            if up != state.gateway or stale:
                await apply_all(app, [{"source": "omniroute", "type": "gateway_up" if up else "gateway_down"}] + stale)
                log(app, f"omniroute {'prendido' if up else 'apagado'}")
                schedule_save(app)
            await asyncio.sleep(cfg.get("every", 5))


def _recent_logs(root):
    """Archivos de los dos últimos días de call_logs (a medianoche escribe en la carpeta nueva)."""
    try:
        days = sorted(d.path for d in os.scandir(root) if d.is_dir())[-2:]
    except OSError:
        return []
    out = []
    for d in days:
        try:
            out += [e.path for e in os.scandir(d) if e.name.endswith(".json")]
        except OSError:
            pass
    return out


async def calls_loop(app, cfg):
    """Sigue los call_logs de OmniRoute (calls.py): cada request nueva de Codex o Gemini mueve a Leonard o Penny."""
    root = Path(os.path.expanduser(cfg.get("call_logs", "~/.omniroute/call_logs")))
    clients, idle_ms = cfg.get("clients"), cfg.get("idle", 20) * 1000
    seen = set(_recent_logs(root))   # lo de antes de arrancar no se repite
    tries, last = {}, {}             # archivo -> intentos de leerlo; source -> ts de su última request
    while True:
        await asyncio.sleep(cfg.get("calls_every", 1))
        state, changed = app["state"], False
        for path in sorted(p for p in _recent_logs(root) if p not in seen):
            data = read_log(Path(path))
            if data is None and tries.get(path, 0) < 5:   # a medio escribir: se reintenta
                tries[path] = tries.get(path, 0) + 1
                continue
            seen.add(path)
            tries.pop(path, None)
            ev = normalize(event_of(data, clients)) if data else None
            if ev is None:
                continue
            if app["procs"] is not None:
                # Solo se mueve si su programa está abierto (si no, una request suelta no lo hace entrar)
                if "proc" not in state.agents.get(ev["source"], {}).get("sessions", {}):
                    continue
                ev["session"] = "proc"
            last[ev["source"]] = ev["ts"]
            if state.apply(ev):
                await broadcast(app, {"type": "event", "event": ev})
            log(app, f"omniroute: {ev['source']} {ev['type']}{' ' + ev['tool'] if 'tool' in ev else ''}")
            changed = True
        for source, ts in list(last.items()):
            if now_ms() - ts > idle_ms:   # sin requests un rato: terminó el turno
                del last[source]
                a = state.agents.get(source)
                if a and a["present"] and a["state"] != "idle":
                    ev = normalize({"source": source, "type": "turn_end", "session": "proc"})
                    if state.apply(ev):
                        await broadcast(app, {"type": "event", "event": ev})
                    changed = True
        if changed:
            schedule_save(app)


async def on_startup(app):
    app["timers"]["prune"] = asyncio.create_task(prune_loop(app))
    if app["procs"] is not None:
        await check_procs(app, app["procs"], 1)   # antes de atender: lo guardado de antes no vale
        app["timers"]["procs"] = asyncio.create_task(procs_loop(app, app["procs"]))
    if app["omniroute"].get("enabled", True):
        app["timers"]["gateway"] = asyncio.create_task(gateway_loop(app, app["omniroute"]))
        app["timers"]["calls"] = asyncio.create_task(calls_loop(app, app["omniroute"]))


async def on_cleanup(app):
    for t in app["timers"].values():
        if t is not None:
            t.cancel()
    save_now(app)
    for ws in list(app["clients"]):
        await ws.close()
    try:
        if json.loads(RUNNING.read_text(encoding="utf-8")).get("pid") == os.getpid():
            RUNNING.unlink()
    except (OSError, ValueError):
        pass


def make_app(port, quiet=False):
    try:
        config = json.loads((PUBLIC / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    state = State(config.get("tool_roles"))
    state.load(STATE_FILE)
    app = web.Application(client_max_size=MAX_BODY, middlewares=[no_cache])
    procs = config.get("processes") or {}
    app.update(state=state, clients=set(), port=port, quiet=quiet, timers={}, omniroute=config.get("omniroute") or {},
               procs=procs if procs.get("enabled", True) else None, proc_missing={})
    app.router.add_get("/ws", ws_handler)
    app.router.add_post("/event", event_handler)
    app.router.add_get("/state", state_handler)
    app.router.add_get("/", index_handler)
    app.router.add_static("/", PUBLIC)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main():
    ap = argparse.ArgumentParser(description="Servidor del wallpaper: estáticos + /ws + /event + /state")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("WALLPAPER_PORT", 8765)))
    ap.add_argument("--quiet", action="store_true", help="sin log de eventos")
    args = ap.parse_args()
    # Con pythonw no hay consola: el log se descarta
    quiet = args.quiet or sys.stdout is None
    asyncio.run(serve(make_app(args.port, quiet), args.host, args.port, quiet))


async def serve(app, host, port, quiet):
    """Como web.run_app, pero .running.json se escribe recién cuando el puerto escucha: si otro servidor ya lo
    tiene, este se va sin tocarle el archivo (dos hooks pueden arrancar dos a la vez)."""
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    try:
        await web.TCPSite(runner, host, port).start()
    except OSError:
        await runner.cleanup()
        return
    RUNNING.write_text(json.dumps({"port": port, "pid": os.getpid()}), encoding="utf-8")
    if not quiet:
        print(f"escuchando en http://{host}:{port}/", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    main()
