"""¿Qué IAs están abiertas? Procesos de Windows y de WSL -> {"claude", "codex", "gemini"}.

Decide quién está en el living: el personaje se queda mientras su programa esté abierto (aunque no haga nada) y
se va cuando se cierra. Los hooks y los call_logs solo dicen qué está haciendo.

- Windows (psutil, o tasklist si no está): claude.exe (app de Claude y Claude Code), codex.exe (app de Codex y
  Codex CLI), y un node que corre gemini (Gemini CLI instalado en Windows).
- WSL: solo las distros que ya están corriendo (`wsl -l -q --running`: nunca prende una). Adentro `ps`: un node
  que corre .../gemini o .../codex, o el binario codex. `gemini_debug_mcp.py` (un MCP de Codex) no cuenta.

config.json -> processes: {"windows": {nombre.exe: source}, "scripts": {nombre de script: source}}.
"""

import os
import subprocess

DEFAULT_WINDOWS = {"claude.exe": "claude", "codex.exe": "codex"}
DEFAULT_SCRIPTS = {"gemini": "gemini", "codex": "codex"}
NO_WINDOW = 0x08000000 if os.name == "nt" else 0   # CREATE_NO_WINDOW: con pythonw no parpadea una consola


def _run(args, timeout=3, encoding="utf-8"):
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout, creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode(encoding, "replace") if r.returncode == 0 else None


def _script_source(argv, scripts):
    """node /usr/local/bin/gemini --model X -> "gemini". Solo el primer argumento que no es una opción."""
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        name = arg.replace("\\", "/").rsplit("/", 1)[-1].lower()
        for suffix in (".js", ".mjs", ".cmd"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        return scripts.get(name)
    return None


def _windows(windows, scripts):
    found, has_wsl = set(), False
    try:
        import psutil
    except ImportError:
        psutil = None
    if psutil:
        for p in psutil.process_iter(["name"]):
            name = (p.info["name"] or "").lower()
            if name in windows:
                found.add(windows[name])
            elif name == "wslhost.exe":
                has_wsl = True
            elif name == "node.exe":
                try:
                    s = _script_source(p.cmdline(), scripts)
                except (psutil.Error, OSError):
                    s = None
                if s == "gemini":   # el codex de node en Windows termina lanzando codex.exe
                    found.add(s)
        return found, has_wsl
    out = _run(["tasklist", "/fo", "csv", "/nh"], encoding="mbcs" if os.name == "nt" else "utf-8")
    for line in (out or "").splitlines():
        name = line.split('","', 1)[0].strip('"').lower()
        if name in windows:
            found.add(windows[name])
        elif name == "wslhost.exe":
            has_wsl = True
    return found, has_wsl


def _wsl(scripts):
    found = set()
    out = _run(["wsl.exe", "-l", "-q", "--running"], encoding="utf-16-le")
    for distro in (d.strip().strip("\0") for d in (out or "").splitlines()):
        if not distro:
            continue
        ps = _run(["wsl.exe", "-d", distro, "--exec", "ps", "-eo", "comm=,args="])
        for line in (ps or "").splitlines():
            parts = line.split()
            if not parts:
                continue
            comm = parts[0].lower()
            if comm in scripts and comm != "gemini":   # el binario nativo de codex
                found.add(scripts[comm])
            elif comm == "node":
                s = _script_source(parts[1:], scripts)
                if s:
                    found.add(s)
    return found


def running(cfg=None):
    """Sources con su programa abierto ahora."""
    cfg = cfg or {}
    windows = {k.lower(): v for k, v in (cfg.get("windows") or DEFAULT_WINDOWS).items() if not k.startswith("_")}
    scripts = {k.lower(): v for k, v in (cfg.get("scripts") or DEFAULT_SCRIPTS).items() if not k.startswith("_")}
    found, has_wsl = _windows(windows, scripts)
    if has_wsl and os.name == "nt" and cfg.get("wsl", True):
        found |= _wsl(scripts)
    return found


if __name__ == "__main__":
    print(sorted(running()))
