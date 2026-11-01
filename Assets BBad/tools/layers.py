"""Capas de primer plano: muebles recortados del fondo que se dibujan encima de quien queda detrás.

theme.json -> scene.layers: {"mueble": {"pos": [x, y], "tiles": {"a": [[b0, b1]]}}}
Imágenes en aligned/layers/<fondo>/<mueble>.png (las genera el cut_layers.py del tema).

Un mueble tapa a un personaje en la casilla (a, b) si su huella tiene alguna casilla (a', b')
con a' >= a y b' >= b, o sea más cerca de la cámara en los dos ejes, y el personaje no está
parado sobre la huella (los asientos del sillón son parte de la huella: sentado se ve delante).
"""
import numpy as np
from PIL import Image


def _tiles(spec):
    return {(int(a), b) for a, runs in spec["tiles"].items() for b0, b1 in runs for b in range(b0, b1 + 1)}


def _prop(th, spec, bg):
    """Imagen de un objeto agregado (scene.props), con la luz del fondo bg.

    De noche se multiplica por cuánto cambia el fondo alrededor respecto del de día.
    """
    img = Image.open(th.dir / spec["image"]).convert("RGBA")
    if bg == "day":
        return img
    x, y = spec["pos"]
    box = (x - 20, y - 20, x + img.width + 20, y + img.height + 20)
    day = np.asarray(Image.open(th.aligned / "day.png").convert("RGB").crop(box), float).mean(axis=(0, 1))
    now = np.asarray(Image.open(th.aligned / f"{bg}.png").convert("RGB").crop(box), float).mean(axis=(0, 1))
    a = np.asarray(img, float)
    a[..., :3] = np.clip(a[..., :3] * (now / np.maximum(day, 1)), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def load(th, bg):
    """Capas del fondo bg como [{"name", "img", "pos", "tiles"}]; [] si el tema no tiene.
    Incluye los objetos agregados (scene.props): también tapan a quien queda detrás."""
    out = []
    for name, spec in (th.scene.get("layers") or {}).items():
        if name.startswith("_"):
            continue
        path = th.aligned / "layers" / bg / f"{name}.png"
        if not path.exists():
            continue
        tiles = _tiles(spec)
        out.append({"name": name, "img": Image.open(path).convert("RGBA"), "pos": tuple(spec["pos"]),
                    "tiles": tiles, "depth": max(a + b for a, b in tiles)})
    for name, spec in (th.scene.get("props") or {}).items():
        tiles = _tiles(spec)
        out.append({"name": name, "img": _prop(th, spec, bg), "pos": tuple(spec["pos"]),
                    "tiles": tiles, "depth": max(a + b for a, b in tiles)})
    return out


def background(th, bg):
    """Fondo alineado bg con los objetos agregados (scene.props) pintados encima."""
    img = Image.open(th.aligned / f"{bg}.png").convert("RGBA")
    for spec in (th.scene.get("props") or {}).values():
        img.alpha_composite(_prop(th, spec, bg), tuple(spec["pos"]))
    return img


def covers(layer, tile):
    """True si el mueble queda delante de un personaje en esa casilla."""
    if tile in layer["tiles"]:
        return False
    a, b = tile
    return any(la >= a and lb >= b for la, lb in layer["tiles"])


def _box(pos, img):
    return pos[0], pos[1], pos[0] + img.width, pos[1] + img.height


def _overlap(p, q):
    return p[0] < q[2] and q[0] < p[2] and p[1] < q[3] and q[1] < p[3]


def compose(img, layers, actors):
    """Dibuja los personajes sobre img (el fondo) y encima los muebles que los tapan.

    actors: [{"sprite": Image RGBA, "pos": (x, y) esquina, "tile": (a, b)}]. Modifica img.
    """
    for a in actors:
        a["box"] = _box(a["pos"], a["sprite"])
    # Solo hace falta redibujar los muebles que tapan a alguien
    active = [l for l in layers
              if any(_overlap(_box(l["pos"], l["img"]), a["box"]) and covers(l, a["tile"]) for a in actors)]
    items = [("actor", a) for a in actors] + [("layer", l) for l in active]
    n = len(items)
    after = {i: set() for i in range(n)}   # i se dibuja antes que cada j de after[i]
    for i in range(n):
        for j in range(i + 1, n):
            (ki, x), (kj, y) = items[i], items[j]
            bx = x["box"] if ki == "actor" else _box(x["pos"], x["img"])
            by = y["box"] if kj == "actor" else _box(y["pos"], y["img"])
            if not _overlap(bx, by):
                continue
            if ki == kj == "actor":
                front = j if (y["pos"][1] + y["sprite"].height) >= (x["pos"][1] + x["sprite"].height) else i
            elif ki == kj == "layer":
                front = j if y["depth"] >= x["depth"] else i
            else:
                act, lay, ia, il = (x, y, i, j) if ki == "actor" else (y, x, j, i)
                front = il if covers(lay, act["tile"]) else ia
            back = i if front == j else j
            after[back].add(front)
    # Orden topológico; si hay un ciclo, sigue por el de pies más abajo
    pending = {i: 0 for i in range(n)}
    for i in after:
        for j in after[i]:
            pending[j] += 1

    def foot(i):
        k, it = items[i]
        return it["pos"][1] + (it["sprite"].height if k == "actor" else it["img"].height)

    done = set()
    while len(done) < n:
        ready = [i for i in range(n) if i not in done and pending[i] == 0]
        i = min(ready or [i for i in range(n) if i not in done], key=foot)
        done.add(i)
        for j in after[i]:
            pending[j] -= 1
        k, it = items[i]
        img.alpha_composite(it["sprite"] if k == "actor" else it["img"], it["pos"])
    return img
