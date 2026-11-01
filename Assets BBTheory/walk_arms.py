"""Balanceo de brazos en las caminatas de Sheldon.

Los brazos de walk (piernas de Leonard + torso de walk_orig, walk_from_leonard.py) no se movían, y los
de walk_back (hoja de Gemini) iban y volvían entre dos poses. Este script separa cada brazo del torso
con una línea por filas (como las piernas en walk_cycle.py) y lo inclina: el hombro queda quieto y la
mano se corre `dx` px (de a poco desde `top` hasta `hand`). Adelante es +x (las dos caminan hacia la
derecha; las de la izquierda se espejan). El brazo de cerca va encima del torso, el de lejos debajo.

Por cuadro: de qué cuadro sale el cuerpo, de cuál los brazos (pueden ser de otro: se borran los
propios y se pegan los del otro) y cuánto se corre cada brazo. Ciclo de péndulo: medio -> adelante ->
medio -> atrás para el brazo de cerca, y lo contrario para el de lejos.

Donde un brazo se separa del torso (o deja al aire una parte del cuerpo) el píxel que queda vacío al
lado de un píxel claro se pinta de contorno: así no quedan bordes sin línea negra ni huecos.

Parte de anims/<anim>_noarms.png (la primera vez copia anims/<anim>.png). walk_from_leonard.py escribe
directamente walk_noarms.png y llama a este script. No rearma el atlas: pega los cuadros nuevos en los
rectángulos de la animación en atlas.png (el resto del atlas no se toca).

    python -I "Assets BBTheory/walk_arms.py"              # walk y walk_back
    python -I "Assets BBTheory/walk_arms.py" walk_back
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
CHARS = HERE / "characters"
OUTLINE = (9, 1, 2)

# arms[cuadro]: brazos de ese cuadro de la base. split: (y, x) del borde con el torso (izquierda: brazo
#   en x < borde; derecha: x > borde; el brazo de cerca se lleva la línea negra que lo separa del torso,
#   así al taparlo la conserva), rows: filas del brazo, top: fila del hombro (no se mueve),
#   hand: fila desde la que se corre entero.
# frames: (cuadro del cuerpo, cuadro de los brazos, dx del brazo izquierdo, dx del derecho)
ARMS = {
    ("Sheldon", "walk"): {
        "near": "left",
        "arms": {
            0: {"left": {"split": [(54, 10), (58, 15), (80, 15)], "rows": (54, 80), "top": 57, "hand": 75},
                "right": {"split": [(52, 34), (72, 34), (73, 38), (78, 38)], "rows": (52, 77), "top": 57, "hand": 73}},
            1: {"left": {"split": [(54, 9), (58, 14), (80, 14)], "rows": (54, 80), "top": 57, "hand": 75},
                "right": {"split": [(52, 33), (78, 33)], "rows": (52, 77), "top": 57, "hand": 73}},
        },
        # 0 y 2: pies juntos (brazos al medio); 1 y 3: zancada (mismo dibujo de piernas), brazos a un
        # lado y al otro
        "frames": [(0, 0, 0, 0), (1, 1, 3, -2), (2, 0, 0, 0), (3, 1, -3, 2)],
    },
    ("Sheldon", "walk_back"): {
        "near": "right",
        "arms": {
            0: {"left": {"split": [(57, 13), (74, 13), (75, 14), (80, 14), (81, 13)], "rows": (57, 81), "top": 59, "hand": 78},
                "right": {"split": [(62, 29), (69, 29), (70, 30), (72, 30), (73, 31), (75, 31), (76, 32), (79, 32),
                                    (80, 33), (82, 33), (83, 34), (84, 34), (85, 33), (86, 33), (87, 34)],
                          "rows": (63, 87), "top": 63, "hand": 83}},
            3: {"left": {"split": [(55, 13), (69, 13)], "rows": (57, 69), "top": 59, "hand": 69},
                "right": {"split": [(63, 30), (69, 30), (70, 31), (71, 32), (72, 33), (73, 33), (74, 34),
                                    (75, 35), (76, 34), (77, 34), (78, 35), (79, 35), (80, 36), (81, 37)],
                          "rows": (63, 81), "top": 63, "hand": 77}},
        },
        # la hoja trae: 0 y 2 brazo de cerca colgando, 1 y 3 adelante. El 3 pasa a ir atrás: lleva los
        # brazos del 0, el de cerca hacia atrás y el de lejos hacia adelante (se esconde tras el torso)
        "frames": [(0, None, 0, 0), (1, None, 0, 0), (2, None, 0, 0), (3, 0, 2, -3)],
    },
}


def boundary(split, y):
    return float(np.interp(y, [p[0] for p in split], [p[1] for p in split]))


def arm_mask(frame, side, a):
    H, W = frame.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    b = np.array([boundary(a["split"], y) for y in range(H)])[:, None]
    m = (frame[..., 3] > 0) & (yy >= a["rows"][0]) & (yy <= a["rows"][1])
    return m & ((xx < b) if side == "left" else (xx > b))


def shifted(frame, mask, a, dx):
    """El brazo inclinado: 0 en el hombro, dx entero desde la mano."""
    H, W = frame.shape[:2]
    out = np.zeros_like(frame)
    ys, xs = np.nonzero(mask)
    t = np.clip((ys - a["top"]) / (a["hand"] - a["top"]), 0, 1)
    xd = xs + np.round(dx * t).astype(int)
    ok = (xd >= 0) & (xd < W)
    out[ys[ok], xd[ok]] = frame[ys[ok], xs[ok]]
    return out


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]


def light(img):
    return (img[..., 3] > 0) & (img[..., :3].max(-1) >= 100)


def arms_of(cfg, i):
    """Brazos del cuadro i (los cuadros sin entrada repiten el dibujo del i % 2)."""
    return cfg["arms"][i] if i in cfg["arms"] else cfg["arms"][i % 2]


def swing(frames, cfg):
    """frames: cuadros de la base (sin balanceo). Devuelve los cuadros con los brazos balanceados."""
    far = "left" if cfg["near"] == "right" else "right"
    out = []
    for body_i, arms_i, dl, dr in cfg["frames"]:
        target = frames[body_i]
        src_i = body_i if arms_i is None else arms_i
        if dl == 0 and dr == 0 and src_i == body_i:
            out.append(target.copy())
            continue
        src = frames[src_i]
        body = target.copy()
        # brazos propios del cuadro fuera (si se reemplazan por los de otro cuadro, o se mueven)
        own = arms_of(cfg, body_i)
        for side in ("left", "right"):
            body[arm_mask(target, side, own[side])] = 0
        arms = arms_of(cfg, src_i)
        layer = {}
        for side, dx in (("left", dl), ("right", dr)):
            layer[side] = shifted(src, arm_mask(src, side, arms[side]), arms[side], dx)
        f = np.zeros_like(target)
        over(f, layer[far])
        over(f, body)
        over(f, layer[cfg["near"]])
        # contorno donde quedó vacío al lado de algo claro (el brazo se separó del torso o al revés)
        was = (target[..., 3] > 0) | (src[..., 3] > 0)
        empty = f[..., 3] == 0
        lt = light(f)
        nb = np.zeros_like(lt)
        nb[1:] |= lt[:-1]; nb[:-1] |= lt[1:]; nb[:, 1:] |= lt[:, :-1]; nb[:, :-1] |= lt[:, 1:]
        fix = empty & was & nb
        f[fix] = (*OUTLINE, 255)
        # píxeles sueltos
        op = f[..., 3] > 0
        n = np.zeros(op.shape, int)
        for dy in (-1, 0, 1):
            for ex in (-1, 0, 1):
                if dy or ex:
                    n += np.roll(np.roll(op, dy, 0), ex, 1)
        f[op & (n == 0)] = 0
        out.append(f)
    return out


def patch_atlas(char, anim, frames):
    """Pega los cuadros en los rectángulos de la animación en atlas.png (lee el atlas recién)."""
    d = CHARS / char
    meta = json.loads((d / "atlas.json").read_text(encoding="utf-8"))
    rects = meta["animations"][anim]["frames"]
    atlas = np.array(Image.open(d / meta["image"]).convert("RGBA"))
    if len(rects) != len(frames) or any((r[2], r[3]) != (f.shape[1], f.shape[0]) for r, f in zip(rects, frames)):
        raise SystemExit(f"{char}/{anim}: el atlas no coincide con los cuadros, rearmarlo con extract_anim.py --rebuild")
    for (x, y, w, h), f in zip(rects, frames):
        atlas[y:y + h, x:x + w] = f
    Image.fromarray(atlas).save(d / meta["image"])


def build(char, anim, atlas=True):
    cfg = ARMS[(char, anim)]
    anim_dir = CHARS / char / "anims"
    info_path = anim_dir / f"{anim}.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    base = anim_dir / f"{anim}_noarms.png"
    if not base.exists():
        base.write_bytes((anim_dir / f"{anim}.png").read_bytes())
    sheet = np.asarray(Image.open(base).convert("RGBA"))
    W, H = info["frame_size"]
    frames = [sheet[:, i * W:(i + 1) * W].copy() for i in range(info["frames"])]
    frames = swing(frames, cfg)

    Image.fromarray(np.concatenate(frames, axis=1)).save(anim_dir / f"{anim}.png")
    big = [Image.fromarray(f).resize((W * 6, H * 6), Image.NEAREST) for f in frames]
    bg = [Image.new("RGBA", b.size, (60, 60, 70, 255)) for b in big]
    for b, im in zip(bg, big):
        b.alpha_composite(im)
    bg[0].convert("RGB").save(anim_dir / f"{anim}_x6.gif", save_all=True, append_images=[b.convert("RGB") for b in bg[1:]],
                              duration=1000 // info["fps"], loop=0)
    info["arms"] = "walk_arms.py"
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    if atlas:
        patch_atlas(char, anim, frames)
    print(f"{char}/{anim}: brazos balanceados")


def main():
    wanted = [w.lower() for w in sys.argv[1:]]
    for char, anim in ARMS:
        if not wanted or anim.lower() in wanted:
            build(char, anim)


if __name__ == "__main__":
    main()
