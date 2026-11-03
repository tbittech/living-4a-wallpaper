"""Idle con respiración y parpadeo, a partir de un solo cuadro quieto.

El idle de Penny salió de un único cuadro de la hoja (`--pick 2,2,2,2`) y quedaba duro. Este script
toma ese cuadro y arma un loop: de la cintura para arriba sube 1 px (respira) y en un cuadro cierra los
ojos. Las piernas y las botas no se mueven, así que el ancla de los pies queda igual.

Parte de anims/idle_orig.png (la primera vez copia anims/idle.png), escribe anims/idle.png, actualiza
frames/fps en anims/idle.json, rearma el atlas y deja un GIF de prueba en anims/idle_preview.gif.

    python -I "Assets BBTheory/idle_breathe.py"
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
CHARS = HERE / "characters"
TOOLS = HERE.parent / "Assets BBad" / "tools"
SKIN = (246, 201, 162, 255)
LASH = (7, 3, 3, 255)

# waist: primera fila que no se mueve (arriba del short). eyes: (x0, x1, y0, y1) de cada ojo abierto,
#   que se pinta de piel, y la fila donde va la rayita del ojo cerrado.
# frames: (sube 1 px, parpadea) por cuadro; 8 cuadros a 4 fps = un respiro por segundo, un parpadeo cada 2 s.
IDLE = {
    "penny": {
        "waist": 72,
        "eyes": [((21, 27, 26, 31), 29), ((32, 37, 26, 28), 27)],
        "frames": [(0, 0), (1, 0), (1, 0), (0, 0), (0, 1), (1, 0), (1, 0), (0, 0)],
        "fps": 4,
    },
}


def blink(f, eyes):
    for (x0, x1, y0, y1), line in eyes:
        f[y0:y1 + 1, x0:x1 + 1] = SKIN
        f[line, x0:x1 + 1] = LASH
    return f


def breathe(f, waist):
    out = f.copy()
    out[:waist - 1] = f[1:waist]
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    name = sys.argv[1] if len(sys.argv) > 1 else "penny"
    cfg = IDLE[name]
    anims = CHARS / name / "anims"
    orig = anims / "idle_orig.png"
    if not orig.exists():
        shutil.copy(anims / "idle.png", orig)
    js = anims / "idle.json"
    info = json.loads(js.read_text(encoding="utf-8"))
    fw, fh = info["frame_size"]
    base = np.array(Image.open(orig).convert("RGBA"))[:, :fw]

    frames = []
    for up, closed in cfg["frames"]:
        f = base.copy()
        if closed:
            f = blink(f, cfg["eyes"])
        if up:
            f = breathe(f, cfg["waist"])
        frames.append(f)
    Image.fromarray(np.concatenate(frames, axis=1)).save(anims / "idle.png")

    info.update(frames=len(frames), fps=cfg["fps"], loop=True)
    js.write_text(json.dumps(info, indent=2), encoding="utf-8")

    scale = 6
    big = [Image.fromarray(f).resize((fw * scale, fh * scale), Image.NEAREST) for f in frames]
    gif = []
    for im in big:
        bg = Image.new("RGBA", im.size, (235, 235, 240, 255))
        bg.alpha_composite(im)
        gif.append(bg.convert("RGB"))
    gif[0].save(anims / "idle_preview.gif", save_all=True, append_images=gif[1:],
                duration=1000 // cfg["fps"], loop=0)

    subprocess.run([sys.executable, "-I", str(TOOLS / "extract_anim.py"), name, "--rebuild",
                    "--theme", "big_bang"], check=True)
    print(f"{name} idle: {len(frames)} cuadros a {cfg['fps']} fps -> {anims / 'idle.png'}")


if __name__ == "__main__":
    main()
