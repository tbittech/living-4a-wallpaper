"""Caminata de Sheldon con las piernas de la de Leonard.

Toma las piernas de characters/leonard/anims/walk.png (debajo del buzo), les cambia los colores
(jean -> pantalón caqui de Sheldon, zapatos marrones -> grises) y las pone debajo de la remera de
Sheldon (torso, cabeza y brazos de anims/walk_orig.png). Sheldon tiene la cadera más alta: el jean se
estira en vertical hasta el ruedo de la remera; los zapatos quedan enteros y apoyados en el piso.
Mismo ciclo que Leonard (4 cuadros, plantado -> zancada -> plantado -> zancada).

Los brazos se balancean después con walk_arms.py (este script deja la base en anims/walk_noarms.png).

La caminata de 8 cuadros anterior queda en source/walk_8f.png.

    python -I "Assets BBTheory/walk_from_leonard.py"
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from walk_cycle import components  # noqa: E402
import walk_arms  # noqa: E402

TOOLS = HERE.parent / "Assets BBad" / "tools"
CHARS = HERE / "characters"

# primera fila de piernas de Leonard (debajo del contorno del buzo) y desde qué fila puede haber zapatos
LEO_TOP = 78
SHOE_ZONE = 86
# cuadro de walk_orig de Sheldon que pone el torso en cada cuadro de Leonard
UPPER = [1, 3, 1, 3]
# filas debajo del ruedo en las que todavía puede haber manos de Sheldon
HANDS = 9

JEAN = {(73, 106, 136): (145, 120, 84), (54, 77, 107): (108, 85, 58), (32, 53, 79): (90, 65, 46)}
SHOE = {(121, 86, 62): (44, 51, 54), (76, 55, 37): (34, 40, 43), (58, 38, 26): (28, 32, 35),
        (177, 158, 148): (154, 152, 151), (164, 119, 96): (116, 115, 115), (204, 154, 125): (116, 115, 115),
        (218, 177, 150): (154, 152, 151), (42, 39, 36): (25, 0, 16), (39, 23, 16): (40, 26, 20),
        (6, 4, 4): (9, 1, 2)}
SKIN = {(243, 197, 157), (218, 177, 150), (230, 202, 178), (204, 154, 125), (164, 119, 96), (177, 158, 148)}
OLIVE = {(87, 86, 51), (118, 119, 71), (94, 93, 61)}


def colors(frame):
    return [[tuple(int(v) for v in px[:3]) for px in row] for row in frame]


def leo_legs(frame):
    """Piernas de Leonard recoloreadas, sin manos; y la fila donde empiezan los zapatos."""
    H, W = frame.shape[:2]
    cols = colors(frame)
    out = np.zeros_like(frame)
    shoe_top = H
    for y in range(LEO_TOP, H):
        jean = [x for x in range(W) if frame[y, x, 3] and cols[y][x] in JEAN]
        for x in range(W):
            if not frame[y, x, 3]:
                continue
            c = cols[y][x]
            if y < SHOE_ZONE:
                # arriba de los zapatos solo va el jean y su contorno: lo que esté lejos es una mano
                if c in SKIN or not jean or x < min(jean) - 1 or x > max(jean) + 1:
                    continue
            elif c in SHOE and c not in ((6, 4, 4), (39, 23, 16)):
                shoe_top = min(shoe_top, y)
            if c in OLIVE:
                c = (61, 39, 28)
            out[y, x, :3] = JEAN.get(c) or SHOE.get(c) or c
            out[y, x, 3] = 255
    # donde estaba la mano: nada a la izquierda del borde de la pierna (el de debajo de la mano), sin
    # píxeles sueltos y con contorno a los costados del jean
    left = np.nonzero(out[SHOE_ZONE, :, 3])[0].min()
    out[LEO_TOP:SHOE_ZONE, :left] = 0
    for y in range(LEO_TOP, SHOE_ZONE):
        for x in range(W):
            if out[y, x, 3] and out[y, x, :3].tolist() not in [list(v) for v in JEAN.values()]:
                n = sum(out[y + dy, x + ex, 3] > 0 for dy, ex in ((-1, 0), (1, 0), (0, -1), (0, 1))
                        if 0 <= x + ex < W)
                if n < 2:
                    out[y, x] = 0
        xs = np.nonzero(out[y, :, 3])[0]
        if len(xs):
            for x, step in ((xs.min(), -1), (xs.max(), 1)):
                if tuple(out[y, x, :3]) in JEAN.values() and 0 <= x + step < W:
                    out[y, x + step] = (9, 1, 2, 255)
    # restos de la mano separados de las piernas
    lab, n = components(out[..., 3] > 0)
    for i in range(1, n + 1):
        if (lab == i).sum() < 20:
            out[lab == i] = 0
    return out, shoe_top


def sheldon_upper(frame):
    """Torso, cabeza y brazos de Sheldon, y la última fila de la remera (ruedo)."""
    H, W = frame.shape[:2]
    rgb = frame[..., :3].astype(int)
    opaque = frame[..., 3] > 0
    red = opaque & (rgb[..., 0] > 90) & (rgb[..., 1] < 40) & (rgb[..., 2] < 40)
    ys, xs = np.nonzero(red)
    hem = ys.max()
    x0, x1 = xs[ys >= hem - 3].min(), xs[ys >= hem - 3].max()
    yy, xx = np.mgrid[0:H, 0:W]
    upper = opaque & ((yy <= hem) | ((yy <= hem + HANDS) & ((xx < x0 - 1) | (xx > x1 + 1))))
    out = np.zeros_like(frame)
    out[upper] = frame[upper]
    return out, hem, (x0, x1)


def narrow(out, top, bottom, width):
    """Leonard es más ancho: angosta el jean hasta el ancho del ruedo de Sheldon en la cintura, menos
    hacia abajo y nada desde los zapatos (cada fila se achica hacia el centro de la cintura)."""
    xs = np.nonzero(out[top, :, 3])[0]
    cx = (xs.min() + xs.max()) / 2
    f0 = min(1.0, width / (xs.max() - xs.min() + 1))
    for y in range(top, bottom):
        f = f0 + (1 - f0) * (y - top) / max(1, bottom - top)
        row = out[y].copy()
        out[y] = 0
        for xd in range(out.shape[1]):
            xs_ = int(round(cx + (xd - cx) / f))
            if 0 <= xs_ < out.shape[1] and row[xs_, 3]:
                out[y, xd] = row[xs_]


def compose(leo, she, dx):
    H = she.shape[0]
    W = she.shape[1]
    legs, shoe_top = leo_legs(leo)
    upper, hem, (x0, x1) = sheldon_upper(she)
    out = np.zeros_like(she)
    # el jean se estira de [LEO_TOP, shoe_top) a [hem + 1, shoe_top); los zapatos van tal cual
    top = hem + 1
    for yd in range(top, H):
        ys = yd if yd >= shoe_top else LEO_TOP + int((yd - top) * (shoe_top - LEO_TOP) / (shoe_top - top))
        for x in range(legs.shape[1]):
            if legs[ys, x, 3] and 0 <= x + dx < W:
                out[yd, x + dx] = legs[ys, x]
    narrow(out, top, shoe_top, x1 - x0 + 1)
    m = upper[..., 3] > 0
    out[m] = upper[m]
    return out


def main():
    leo_info = json.loads((CHARS / "leonard" / "anims" / "walk.json").read_text(encoding="utf-8"))
    anim_dir = CHARS / "Sheldon" / "anims"
    info_path = anim_dir / "walk.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    # fuera de anims/ para que el atlas no la tome como animación
    backup = CHARS / "Sheldon" / "source" / "walk_8f.png"
    if not backup.exists():
        shutil.copyfile(anim_dir / "walk.png", backup)

    leo = np.asarray(Image.open(CHARS / "leonard" / "anims" / "walk.png").convert("RGBA"))
    she = np.asarray(Image.open(anim_dir / "walk_orig.png").convert("RGBA"))
    LW = leo_info["frame_size"][0]
    W, H = she.shape[1] // 4, she.shape[0]
    # el anclaje (los pies) de Leonard cae donde va el de Sheldon
    anchor_x = W // 2 - 1
    dx = anchor_x - leo_info["anchor"][0]
    frames = [compose(leo[:, i * LW:(i + 1) * LW], she[:, s * W:(s + 1) * W], dx) for i, s in enumerate(UPPER)]

    # sin balanceo de brazos: walk_arms.py parte de walk_noarms.png y escribe walk.png y walk_x6.gif
    Image.fromarray(np.concatenate(frames, axis=1)).save(anim_dir / "walk_noarms.png")
    fps = leo_info["fps"]
    info.update({"frames": len(frames), "fps": fps, "frame_size": [W, H], "anchor": [anchor_x, H - 1],
                 "cycle": "walk_from_leonard.py"})
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    walk_arms.build("Sheldon", "walk", atlas=False)
    subprocess.run([sys.executable, "-I", str(TOOLS / "extract_anim.py"), "--rebuild", "sheldon", "--theme", "big_bang"],
                   check=True)


if __name__ == "__main__":
    main()
