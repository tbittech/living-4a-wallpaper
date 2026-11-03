"""Marca la grilla de casillas de la van (tema breaking_bad), recorta la pared de la puerta y lo guarda en theme.json.

La van se ve de costado: la grilla es rectangular, a = profundidad (hacia la cámara) y b = de izquierda
a derecha, con direcciones propias (scene.facings). Píxeles de aligned/ (1342x760).
Correr desde E:\\ProyectosIA:  python -I "Assets BBad/themes/breaking_bad/mark_grid.py"
"""
import json
import re
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, 'Assets BBad/tools')
import numpy as np, cv2  # noqa: E401,E402
from PIL import Image  # noqa: E402
from grid import IsoGrid, tiles_to_rows  # noqa: E402

TH = Path('Assets BBad/themes/breaking_bad')
grid = {"origin": [500, 476], "u": [0, 8], "v": [17, 0]}
# Moverse en b es ir a izquierda/derecha (3/4, espejado a la izquierda); en a, acercarse (3/4) o alejarse (espalda)
facings = {"_comment": "Van de costado: a = profundidad, b = izquierda a derecha.",
           "down_right": {"step": [0, 1], "view": "three_quarter", "flip": False},
           "up_left": {"step": [0, -1], "view": "three_quarter", "flip": True},
           "down_left": {"step": [1, 0], "view": "three_quarter", "flip": True},
           "up_right": {"step": [-1, 0], "view": "back", "flip": False}}
# Piso: franja angosta delante de la mesa (izquierda) y baldosas (derecha), hasta el umbral de la puerta
floor = [(503, 477), (632, 477), (720, 470), (858, 470), (878, 488), (878, 518), (633, 518), (633, 491), (503, 491)]
blockers = {
    'barrels': [(765, 466), (815, 466), (815, 476), (765, 476)],
    'gas': [(818, 466), (852, 466), (852, 476), (818, 476)],
}


def inside(poly, p):
    return cv2.pointPolygonTest(np.array(poly, np.float32), (float(p[0]), float(p[1])), False) >= 0


g = IsoGrid({"grid": grid, "facings": facings})
walk = {(a, b) for a in range(-3, 8) for b in range(-2, 30)
        if inside(floor, g.center(a, b)) and not any(inside(p, g.center(a, b)) for p in blockers.values())}
# lugares: punto del fondo -> casilla y dirección
pts = {
    "door": ((862, 481), "down_left"),        # umbral de la puerta de atrás
    "exit": ((862, 481), "up_right"),
    "lab_right": ((714, 482), "up_left"),     # punta derecha de la mesa, mirando los frascos
    "lab_left": ((540, 482), "down_right"),   # punta izquierda, mirando hacia la mesa
    "bench": ((610, 482), "up_right"),        # de espaldas, anotando sobre la mesa
    "barrels": ((790, 490), "down_right"),
    "window": ((508, 482), "up_right"),       # mirando por la ventana de la izquierda
    "center": ((730, 498), "down_right"),
    "rest_a": ((760, 506), "down_right"),
    "rest_b": ((680, 506), "down_right"),
    "rest_c": ((830, 500), "up_left"),
}
places = {k: {"tile": list(g.tile_at(*p)), "facing": f} for k, (p, f) in pts.items()}
for k, p in places.items():
    assert tuple(p["tile"]) in walk, (k, p["tile"])
# solo lo conectado con la puerta
seed = tuple(places["door"]["tile"]); comp = {seed}; q = deque([seed])
while q:
    a, b = q.popleft()
    for n in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
        if n in walk and n not in comp:
            comp.add(n); q.append(n)
print('sueltas descartadas:', len(walk - comp)); walk = comp
g.walkable = walk
for k, pl in places.items():
    p = g.path(seed, tuple(pl["tile"])); print('  puerta ->', k, 'sin camino' if p is None else f'{len(p)} pasos')

# Pared derecha de la puerta: tapa al que está en el umbral (el sprite sobresale del marco)
wall = [(876, 300), (960, 300), (960, 530), (876, 530)]
mask = np.zeros((760, 1342), np.uint8); cv2.fillPoly(mask, [np.array(wall, np.int32)], 255)
x0, y0, x1, y1 = 876, 300, 960, 530
for bg in ('day', 'night_idle', 'night_active'):
    im = np.asarray(Image.open(TH / 'aligned' / f'{bg}.png').convert('RGBA')).copy()
    im[..., 3] = mask
    out = TH / 'aligned' / 'layers' / bg; out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(im[y0:y1, x0:x1]).save(out / 'door_wall.png')
wall_tiles = [(a, 23) for a in range(-3, 8)]

th = TH / 'theme.json'; data = json.loads(th.read_text(encoding='utf-8'))
sc = data["scene"]
new = {"_comment": "Grilla de la van sobre aligned/ (1342x760): casillas de 17x8 px, a = profundidad, b = izquierda a derecha (mark_grid.py). Lugares = casilla + dirección.",
       "sprite_scale": 2, "grid": grid, "facings": facings, "tiles": tiles_to_rows(walk), "places": places,
       "seats": {"_comment": "Grupos de lugares: un rol que apunta al grupo va al del personaje (owners) o al primero libre.",
                 "lab": ["lab_right", "lab_left"], "rest": ["rest_a", "rest_b", "rest_c"]},
       "owners": {"lab_right": "walter", "rest_a": "walter", "rest_b": "jesse", "rest_c": "saul"},
       "footprints": {"door_wall": tiles_to_rows(wall_tiles)},
       "layers": {"_comment": "Pared a la derecha de la puerta (mark_grid.py): tapa al que entra.",
                  "door_wall": {"pos": [x0, y0], "tiles": tiles_to_rows(wall_tiles)}}}
for k, v in sc.items():
    if k not in ("walkable",):
        new.setdefault(k, v)   # effects y lo que no se marca acá
data["scene"] = new
txt = json.dumps(data, indent=2, ensure_ascii=False)
txt = re.sub(r'\[\s+(-?\d+(?:\.\d+)?),\s+(-?\d+(?:\.\d+)?)\s+\]', r'[\1, \2]', txt)
txt = re.sub(r'\[\s+(\[[^\[\]]*\](?:,\s+\[[^\[\]]*\])*)\s+\]', lambda m: '[' + re.sub(r'\s+', ' ', m.group(1)) + ']', txt)
th.write_text(txt + "\n", encoding='utf-8'); print(len(walk), 'casillas caminables')
