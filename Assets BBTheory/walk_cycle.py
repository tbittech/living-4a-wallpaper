"""Ciclo de caminata con paso a partir de un solo cuadro de zancada.

Gemini dibujó las caminatas de Sheldon con la misma zancada en los 4 cuadros: las piernas no se
mueven y parece que se desliza. Este script toma un cuadro de anims/<anim>.png, separa las dos
piernas y arma

    zancada -> paso (el pie de atrás se adelanta junto al otro, el cuerpo sube 1 px) -> zancada opuesta -> paso

La pierna que se mueve se corre de a poco desde la cadera (nada) hasta el tobillo (todo): el muslo
sigue pegado y el zapato se mueve entero. Corrimientos de más de ~6 px rompen el contorno.

La zancada opuesta (y su paso) espeja las piernas alrededor del eje de la cadera, pero los zapatos
no se espejan: se trasladan enteros al lugar espejado, así siguen apuntando para adelante. La pierna
de cerca sigue tapando a la de lejos, que es lo que corresponde a la otra zancada.

La primera vez guarda el original en anims/<anim>_orig.png y siempre parte de ahí (si se vuelve a
extraer la hoja con extract_anim.py, borrar ese archivo).

    python -I "Assets BBTheory/walk_cycle.py"            # todas las de CYCLES
    python -I "Assets BBTheory/walk_cycle.py" sheldon:walk
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "Assets BBad" / "tools"

# base: cuadro de la hoja que se usa (0 = el primero)
# split: puntos (y, x) de la línea que separa la pierna izquierda de la derecha (se interpola)
# hip / ankle: filas donde la pierna empieza a correrse y desde donde se corre entera (zapato)
# move: pierna que da el paso y cuánto se corre el pie (dx, dy); front: pierna que se dibuja adelante
# arms: balanceo de brazos; left / right: (y, x) del borde entre cada brazo y el torso (izquierda: x menor
#       que el borde; derecha: mayor), top / hand: filas del hombro (no se mueve) y de la mano (se corre dx)
# (walk_back de Sheldon ya no va: tiene hoja de Gemini con las piernas alternadas, source/walk_back_alt.png)
# swap: zancada opuesta; top: desde qué fila se espeja (debajo de las manos), shoe_top: desde dónde
#       se buscan los zapatos, axis: x del eje de la cadera
CYCLES = {
    ("Sheldon", "walk"): {
        # de frente a la derecha: la izquierda es la de atrás (pie más arriba), la tapa la derecha
        "base": 1,
        "split": [(87, 20), (96, 22), (102, 23), (106, 24)],
        "hip": 87, "ankle": 96,
        "move": ("left", 6, 2), "front": "right",
        "swap": {"top": 80, "shoe_top": 96, "axis": 24},
        "arms": {"top": 54, "hand": 74, "dx": 3,
                 "left": [(54, 14), (79, 14)], "right": [(54, 33), (67, 33), (68, 34), (79, 34)]},
    },
}


def boundary(split, y):
    ys = [p[0] for p in split]
    xs = [p[1] for p in split]
    return float(np.interp(y, ys, xs))


def leg_masks(frame, cfg):
    """Píxeles de cada pierna (debajo de la cadera, a cada lado de la línea split)."""
    H, W = frame.shape[:2]
    alpha = frame[..., 3] > 0
    yy, xx = np.mgrid[0:H, 0:W]
    below = yy >= cfg["hip"]
    bx = np.array([boundary(cfg["split"], y) for y in range(H)])[:, None]
    return {"left": alpha & below & (xx < bx), "right": alpha & below & (xx >= bx)}


def step_leg(frame, mask, dx, dy, cfg):
    """La pierna corrida: 0 en la cadera, (dx, dy) entero desde el tobillo. Rellena las filas que se estiran."""
    H, W = frame.shape[:2]
    out = np.zeros_like(frame)
    hip, ankle = cfg["hip"], cfg["ankle"]
    prev = None
    for y in sorted(set(np.nonzero(mask)[0])):
        t = min(max((y - hip) / (ankle - hip), 0.0), 1.0)
        sx, sy = round(dx * t), round(dy * t)
        xs = np.nonzero(mask[y])[0]
        # si la fila destino saltó más de una, repetir esta fila para no dejar huecos
        targets = range(prev + 1, y + sy + 1) if prev is not None and y + sy > prev + 1 else [y + sy]
        for yd in targets:
            if 0 <= yd < H:
                xd = xs + sx
                ok = (xd >= 0) & (xd < W)
                out[yd, xd[ok]] = frame[y, xs[ok]]
        prev = y + sy
    return out


def components(mask):
    """Componentes conexas (8 vecinos) de una máscara: (etiquetas, cantidad)."""
    H, W = mask.shape
    lab = np.zeros(mask.shape, int)
    n = 0
    for y, x in zip(*np.nonzero(mask)):
        if lab[y, x]:
            continue
        n += 1
        lab[y, x] = n
        stack = [(y, x)]
        while stack:
            cy, cx = stack.pop()
            for ny in (cy - 1, cy, cy + 1):
                for nx in (cx - 1, cx, cx + 1):
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n
                        stack.append((ny, nx))
    return lab, n


def shoe_masks(frame, shoe_top):
    """Cada zapato: núcleo gris + lo pegado a 2 px (contorno negro y, debajo de su mitad, la suela)."""
    rgb = frame[..., :3].astype(int)
    opaque = frame[..., 3] > 0
    black = opaque & (rgb.max(-1) < 50)
    gray = opaque & (rgb.max(-1) - rgb.min(-1) < 25) & ~black
    gray[:shoe_top] = False
    lab, n = components(gray)
    shoes = []
    for i in range(1, n + 1):
        core = lab == i
        if core.sum() < 15:
            continue
        low = np.zeros_like(core)
        low[int(np.nonzero(core)[0].mean()):] = True
        m = core.copy()
        for _ in range(2):
            d = m.copy()
            d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
            d[1:, 1:] |= m[:-1, :-1]; d[1:, :-1] |= m[:-1, 1:]
            m |= d & (black | (opaque & low))
        m[:shoe_top] = False
        shoes.append(m)
    return shoes


def swap_legs(frame, cfg):
    """La otra zancada: piernas espejadas alrededor de la cadera, zapatos trasladados sin espejar."""
    sw = cfg["swap"]
    H, W = frame.shape[:2]
    shoes = shoe_masks(frame, sw["shoe_top"])
    any_shoe = np.zeros((H, W), bool)
    for m in shoes:
        any_shoe |= m
    out = frame.copy()
    out[sw["top"]:] = 0
    ys, xs = np.nonzero((frame[..., 3] > 0) & ~any_shoe)
    keep = ys >= sw["top"]
    ys, xs = ys[keep], xs[keep]
    xd = np.round(2 * sw["axis"] - xs).astype(int)
    ok = (xd >= 0) & (xd < W)
    out[ys[ok], xd[ok]] = frame[ys[ok], xs[ok]]
    # el zapato de la pierna de cerca va último (encima)
    shoes.sort(key=lambda m: np.nonzero(m)[1].mean(), reverse=cfg["front"] == "left")
    for m in shoes:
        ys, xs = np.nonzero(m)
        dx = int(round(2 * sw["axis"] - (xs.min() + xs.max())))
        ok = (xs + dx >= 0) & (xs + dx < W)
        out[ys[ok], xs[ok] + dx] = frame[ys[ok], xs[ok]]
    return out


def swing_arms(frame, cfg, sign):
    """Brazos balanceados: con sign=1 el de la izquierda va adelante (+dx) y el de la derecha atrás.

    El brazo de la izquierda de la imagen es el de cerca (va encima del torso); el de la derecha, debajo.
    """
    am = cfg["arms"]
    H, W = frame.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    opaque = frame[..., 3] > 0
    rows = (yy >= am["top"]) & (yy <= max(p[0] for p in am["left"] + am["right"]))
    lb = np.array([boundary(am["left"], y) for y in range(H)])[:, None]
    rb = np.array([boundary(am["right"], y) for y in range(H)])[:, None]
    left = opaque & rows & (xx < lb) & (yy <= am["left"][-1][0])
    right = opaque & rows & (xx > rb) & (yy <= am["right"][-1][0])
    body = frame.copy()
    body[left | right] = 0

    def moved(mask, dx, away, out):
        """Dibuja el brazo corrido; si se aleja del torso, copias intermedias tapan el hueco que deja."""
        ys, xs = np.nonzero(mask)
        t = np.clip((ys - am["top"]) / (am["hand"] - am["top"]), 0, 1)
        steps = range(0, dx + 1) if dx >= 0 else range(0, dx - 1, -1)
        for k in (steps if away else [dx]):
            xd = xs + np.round(k * t).astype(int)
            ok = (xd >= 0) & (xd < W)
            out[ys[ok], xd[ok]] = frame[ys[ok], xs[ok]]
        return out

    out = np.zeros_like(frame)
    moved(right, -sign * am["dx"], sign < 0, out)
    moved(left, sign * am["dx"], sign < 0, out)
    over(out, body)
    near = np.zeros_like(frame)
    ys, xs = np.nonzero(left)
    t = np.clip((ys - am["top"]) / (am["hand"] - am["top"]), 0, 1)
    xd = xs + np.round(sign * am["dx"] * t).astype(int)
    ok = (xd >= 0) & (xd < W)
    near[ys[ok], xd[ok]] = frame[ys[ok], xs[ok]]
    over(out, near)
    return out


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]


def build(char, anim, cfg):
    anim_dir = HERE / "characters" / char / "anims"
    info_path = anim_dir / f"{anim}.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    orig = anim_dir / f"{anim}_orig.png"
    if not orig.exists():
        orig.write_bytes((anim_dir / f"{anim}.png").read_bytes())
    sheet = np.asarray(Image.open(orig).convert("RGBA"))
    W, H = info["frame_size"]
    frame = sheet[:, cfg["base"] * W:(cfg["base"] + 1) * W].copy()

    masks = leg_masks(frame, cfg)
    leg, dx, dy = cfg["move"]
    other = "right" if leg == "left" else "left"
    body = frame.copy()
    body[masks[leg]] = 0
    stepped = step_leg(frame, masks[leg], dx, dy, cfg)
    passing = np.zeros_like(frame)
    if cfg["front"] == leg:
        over(passing, body)
        over(passing, stepped)
    else:
        over(passing, stepped)
        over(passing, body)
    # en el paso el cuerpo sube 1 px (todo el cuadro: si no, la pierna se corta en el tobillo)
    passing = np.roll(passing, -1, axis=0)
    if "swap" in cfg:
        b = swap_legs(frame, cfg)
        if "arms" in cfg:
            frames = [swing_arms(frame, cfg, 1), passing, swing_arms(b, cfg, -1), swap_legs(passing, cfg)]
        else:
            frames = [frame, passing, b, swap_legs(passing, cfg)]
    else:
        frames = [frame, passing, frame, passing]

    Image.fromarray(np.concatenate(frames, axis=1)).save(anim_dir / f"{anim}.png")
    big = [Image.fromarray(f).resize((W * 6, H * 6), Image.NEAREST) for f in frames]
    bg = [Image.new("RGBA", b.size, (60, 60, 70, 255)) for b in big]
    for b, im in zip(bg, big):
        b.alpha_composite(im)
    bg[0].convert("RGB").save(anim_dir / f"{anim}_x6.gif", save_all=True, append_images=[b.convert("RGB") for b in bg[1:]],
                              duration=1000 // info["fps"], loop=0)
    info["cycle"] = "walk_cycle.py"
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"{char}/{anim}: zancada{'s alternadas' if 'swap' in cfg else ''} y paso desde el cuadro {cfg['base'] + 1}")


def main():
    wanted = [w.lower() for w in sys.argv[1:]]
    chars = set()
    for (char, anim), cfg in CYCLES.items():
        if wanted and f"{char.lower()}:{anim}" not in wanted:
            continue
        build(char, anim, cfg)
        chars.add(char)
    for char in chars:
        subprocess.run([sys.executable, "-I", str(TOOLS / "extract_anim.py"), "--rebuild", char.lower(), "--theme", "big_bang"], check=True)


if __name__ == "__main__":
    main()
