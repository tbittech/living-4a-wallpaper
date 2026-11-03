"""Genera la hoja de una animación con la skill imagen, armando el prompt desde PROMPTS.md del personaje.

Prompt = bloque "Base" + bloque **<anim>** de characters/<p>/PROMPTS.md (+ --extra).
Referencias: la hoja del personaje (source/<p>.jpg o la primera de source/ que no sea una animación)
y la misma animación de Sheldon/Penny de Big Bang (o --pose). Guarda en source/<anim>[_N].<ext>.

    python -I "Assets BBad/themes/breaking_bad/gen_anim.py" walter walk [--pose RUTA] [--extra "..."] [--tag 2]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BBT = HERE.parent.parent.parent / "Assets BBTheory" / "characters"
SCRIPT = Path(os.environ["USERPROFILE"]) / ".claude" / "skills" / "imagen" / "scripts" / "generar_imagen.ps1"
SHEETS = {"walter": "walt.jpg", "jesse": "jessejoy.jpg", "saul": "saul.jpg"}
# Pose de referencia de Big Bang por animación (cook -> type de pie no hay: se usa read)
POSES = {"walk": "Sheldon/source/walk.webp", "walk_back": "Sheldon/source/walk_back.webp",
         "idle": "Sheldon/source/idle.webp", "wave": "Sheldon/source/wave.webp",
         "write": "Sheldon/source/write.webp", "read": "Sheldon/source/read.webp",
         "think": "Sheldon/source/think.webp", "look": "Sheldon/source/write.webp",
         "cook": "Sheldon/source/read.webp", "celebrate": "penny/source/celebrate.png",
         "argue": "penny/source/argue.png"}
# Pose propia de un personaje (Jesse prende un pucho en el idle: manos a la cara)
POSES_BY = {("jesse", "idle"): "Sheldon/source/think.webp"}


def block(text, title):
    head = r"^## Base[^\n]*" if title == "Base" else r"^\*\*%s\*\*[ \t]*" % re.escape(title)
    pat = head + r"\s*```\n(.*?)```"
    m = re.search(pat, text, re.S | re.M)
    if not m:
        raise SystemExit(f"PROMPTS.md no tiene el bloque {title}")
    return m.group(1).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("anim")
    ap.add_argument("--pose", help="hoja de pose de referencia (por defecto la de Big Bang)")
    ap.add_argument("--extra", default="", help="texto que se agrega al final del prompt")
    ap.add_argument("--tag", default="", help="sufijo del archivo de salida (otro intento)")
    ap.add_argument("--models", default="Imagen", help="modelos o combo de OmniRoute (Imagen: round-robin entre cuentas)")
    a = ap.parse_args()
    d = HERE / "characters" / a.character
    text = (d / "PROMPTS.md").read_text(encoding="utf-8")
    prompt = block(text, "Base") + "\n" + block(text, a.anim) + ("\n" + a.extra if a.extra else "")
    refs = [str(d / "source" / SHEETS[a.character])]
    pose = POSES_BY.get((a.character, a.anim)) or POSES.get(a.anim)
    pose = a.pose or (str(BBT / pose) if pose else None)
    if pose:
        refs.append(pose)
    out = d / "source" / (a.anim + (f"_{a.tag}" if a.tag else ""))
    # -File no arma arreglos: -Command con las rutas entre comillas simples y el prompt por variable de entorno
    q = lambda x: "'" + str(x).replace("'", "''") + "'"
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
           f"& {q(SCRIPT)} -Prompt $env:GEN_PROMPT -Ref {','.join(q(r) for r in refs)} -Out {q(out)} -Models {','.join(q(m) for m in a.models.split(','))} -TimeoutSec 540; exit $LASTEXITCODE"]
    os.environ["GEN_PROMPT"] = prompt
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
