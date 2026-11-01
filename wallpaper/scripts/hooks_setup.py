"""Pone (o saca) los hooks del wallpaper en el settings.json de Claude Code, con la ruta real de esta carpeta.

    python wallpaper/scripts/hooks_setup.py install     (lo llama install.ps1)
    python wallpaper/scripts/hooks_setup.py remove      (lo llama uninstall.ps1)
    ... --settings OTRO.json                            (pruebas: otro archivo en vez de ~/.claude/settings.json)

Los eventos y matchers salen de hooks/settings_snippet.json. Antes de poner, saca cualquier hook que apunte a un
cc_hook.py (así, si la carpeta se mueve, correrlo de nuevo actualiza la ruta). No toca los demás hooks ni claves.
El comando usa el python con el que se corre este script (ruta completa: no depende del PATH ni del alias de la
Store). Guarda una copia en settings.json.bak-wallpaper antes de escribir.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = (HERE.parent / "hooks" / "cc_hook.py").resolve()
SNIPPET = HERE.parent / "hooks" / "settings_snippet.json"


def is_ours(hook):
    return "cc_hook.py" in hook.get("command", "")


def strip(hooks):
    """Saca nuestros hooks; borra los grupos y eventos que quedan vacíos."""
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            g["hooks"] = [h for h in g.get("hooks", []) if not is_ours(h)]
            if g["hooks"]:
                groups.append(g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["install", "remove"])
    ap.add_argument("--settings", default=os.path.join(os.path.expanduser("~"), ".claude", "settings.json"))
    args = ap.parse_args()

    path = Path(args.settings)
    settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    hooks = settings.setdefault("hooks", {})
    strip(hooks)

    if args.action == "install":
        command = f'"{Path(sys.executable).as_posix()}" -I -S "{HOOK.as_posix()}"'
        snippet = json.loads(SNIPPET.read_text(encoding="utf-8"))["hooks"]
        for event, groups in snippet.items():
            for g in groups:
                group = {k: v for k, v in g.items() if k != "hooks"}
                group["hooks"] = [{**h, "command": command} for h in g["hooks"]]
                hooks.setdefault(event, []).append(group)
    if not hooks:
        del settings["hooks"]

    if path.exists():
        shutil.copyfile(path, str(path) + ".bak-wallpaper")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Hooks {'puestos' if args.action == 'install' else 'sacados'}: {path}")


if __name__ == "__main__":
    main()
