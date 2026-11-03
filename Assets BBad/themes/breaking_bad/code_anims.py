"""Animaciones básicas hechas por código desde las vistas de referencia (mientras no haya hojas de Gemini).

    idle       3/4: respira (de la cintura para arriba sube 1 px en los cuadros 2 y 3)
    walk       3/4: piernas que alternan (zancada, paso, zancada opuesta, paso)
    walk_back  lo mismo con la vista de espaldas

Las piernas se separan por la columna del medio de la entrepierna; cada una se corre de a poco desde la
cadera (nada) hasta el pie (todo), como walk_cycle.py de Big Bang. No pisa una animación que venga de una
hoja (anims/<anim>.json con "source" distinto de "code"), salvo con --force.

    python -I "Assets BBad/themes/breaking_bad/code_anims.py" [personaje ...] [--only walk,idle] [--force]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
CHARS = HERE / "characters"
TOOLS = HERE.parent.parent / "tools"


def legs(a):
    """(cadera, pie, columna que separa las piernas) de un sprite RGBA (alfa > 0 = opaco)."""
    op = a[..., 3] > 0
    rows = np.nonzero(op.any(axis=1))[0]
    foot = rows.max()
    # Columna de la entrepierna: la más vacía en las filas de los pies, cerca del centro
    low = op[foot - 3:foot + 1]
    cols = np.nonzero(low.any(axis=0))[0]
    mid = (cols.min() + cols.max()) / 2
    hip = foot - max(8, int(len(rows) * 0.2))
    gap_rows = [y for y in range(foot, foot - len(rows) // 3, -1)
                if (lambda xs: len(xs) and (np.diff(xs) > 1).any())(np.nonzero(op[y])[0])]
    if gap_rows:
        hip = min(hip, min(gap_rows) - 2)
        xs = np.nonzero(op[max(gap_rows)])[0]
        k = int(np.argmax(np.diff(xs)))
        mid = (xs[k] + xs[k + 1]) / 2
    return hip, foot, mid


def stride(a, d, hip, foot, mid):
    """Cuadro de zancada: la pierna de la derecha se corre d px y la de la izquierda -d (de a poco)."""
    out = a.copy()
    out[hip:foot + 1] = 0
    h, w = a.shape[:2]
    # primero la de atrás (la que va hacia -x en 3/4), después la de adelante
    for side, sign in (("left", -1), ("right", 1)):
        for y in range(hip, foot + 1):
            off = int(round(sign * d * (y - hip) / max(1, foot - hip)))
            for x in range(w):
                if (x < mid) != (side == "left") or a[y, x, 3] == 0:
                    continue
                nx = x + off
                if 0 <= nx < w:
                    out[y, nx] = a[y, x]
    return out


def lift(a, cut, dy=1):
    """De la fila cut para arriba sube dy px; la fila del corte se repite para no dejar hueco."""
    out = a.copy()
    out[:cut - dy] = a[dy:cut]
    out[cut - dy:cut] = a[cut - 1:cut]
    return out


def save(cdir, name, frames, fps, loop):
    h, w = frames[0].shape[:2]
    strip = np.concatenate(frames, axis=1)
    (cdir / "anims").mkdir(exist_ok=True)
    Image.fromarray(strip, "RGBA").save(cdir / "anims" / f"{name}.png")
    meta = {"source": "code", "frames": len(frames), "fps": fps, "loop": loop, "frame_size": [w, h],
            "anchor": [w // 2, h - 1], "keep_y": False, "pick": None, "lower": 0, "shift": 0}
    (cdir / "anims" / f"{name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chars", nargs="*", default=["walter", "jesse", "saul"])
    ap.add_argument("--only", default="idle,walk,walk_back")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    for c in args.chars:
        cdir = CHARS / c
        made = []
        for name in args.only.split(","):
            j = cdir / "anims" / f"{name}.json"
            if j.exists() and not args.force and json.loads(j.read_text(encoding="utf-8")).get("source") != "code":
                print(f"{c}: {name} viene de una hoja, no se pisa")
                continue
            view = "back" if name == "walk_back" else "three_quarter"
            a = np.asarray(Image.open(cdir / f"{view}.png").convert("RGBA")).copy()
            hip, foot, mid = legs(a)
            if name == "idle":
                f1 = lift(a, hip)
                save(cdir, name, [a, f1, f1, a], 3, True)
            else:
                d = 2
                s1, s2 = stride(a, d, hip, foot, mid), stride(a, -d, hip, foot, mid)
                save(cdir, name, [s1, lift(a, hip), s2, lift(a, hip)], 6, True)
            made.append(name)
        if made:
            subprocess.run([sys.executable, "-I", str(TOOLS / "extract_anim.py"), "--rebuild", c,
                            "--theme", "breaking_bad"], check=True)
            print(f"{c}: {', '.join(made)}")


if __name__ == "__main__":
    main()
