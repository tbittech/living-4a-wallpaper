"""Recorta los muebles del living en capas de primer plano (tema big_bang) y las registra en theme.json.

Cada mueble tiene un polígono aproximado de su silueta en píxeles de aligned/; GrabCut ajusta el borde
(lo de adentro del polígono achicado es mueble seguro, lo de afuera del polígono es fondo seguro).
La misma máscara recorta los tres fondos alineados: aligned/layers/<fondo>/<mueble>.png.
La huella en casillas sale de scene.footprints (mark_grid.py) o, para las sillas, del lugar que ocupan.
Correr desde E:\\ProyectosIA, después de mark_grid.py:  python -I "Assets BBTheory/cut_layers.py" [MUEBLE ...]
Con nombres, recorta solo esos y deja las demás capas como están.
"""
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

DIR = Path("Assets BBTheory")
BGS = ("day", "night_idle", "night_active")
# mueble -> (silueta aproximada, huella: nombre en footprints o "place:LUGAR")
PIECES = {
    "couch": ([(404, 385), (430, 368), (520, 328), (548, 328), (564, 342), (577, 384), (577, 414), (462, 464),
               (404, 450)], "couch"),
    "box": ([(396, 428), (422, 416), (448, 428), (450, 468), (420, 474), (396, 460)], "box"),
    "side_table": ([(536, 334), (566, 328), (610, 352), (610, 400), (566, 402), (544, 382)], "side_table"),
    "armchair": ([(596, 372), (645, 343), (674, 343), (694, 373), (694, 418), (645, 438), (596, 418)], "armchair"),
    "coffee_table": ([(510, 422), (560, 410), (597, 428), (597, 452), (560, 474), (510, 454)], "coffee_table"),
    "chair": ([(581, 455), (612, 436), (634, 443), (636, 492), (600, 502), (581, 490)], "chair"),
    "column": ([(682, 228), (717, 228), (717, 402), (682, 402)], "column"),
    "island": ([(898, 410), (992, 408), (1024, 498), (1014, 562), (938, 562), (898, 472)], "island"),
    "stool": ([(870, 452), (908, 452), (910, 512), (870, 512)], "stool"),
    "front_desks": ([(453, 512), (572, 512), (608, 536), (608, 515), (678, 515), (680, 522), (812, 522),
                     (840, 532), (842, 622), (453, 622)], "front_desks"),
    "chair_left": ([(500, 494), (548, 494), (550, 532), (500, 532)], "place:desk_left"),
    "chair_right": ([(732, 494), (780, 494), (782, 532), (732, 532)], "place:desk_right"),
    "coat_rack_l": ([(393, 443), (442, 443), (442, 560), (393, 560)], "coat_rack_l"),
    "coat_rack_r": ([(658, 578), (707, 578), (707, 692), (658, 692)], "coat_rack_r"),
    "dna": ([(513, 243), (542, 243), (542, 334), (513, 334)], "dna"),
    # Heladerita verde con la planta: tapa a quien está en el pasillo a los cuartos
    "minifridge": ([(843, 346), (876, 346), (880, 372), (874, 388), (873, 430), (845, 430), (842, 400)], "minifridge"),
}
# Partes beige adentro de un mueble que el borrado de piso se llevaría (almohadones)
KEEP = {"couch": [(408, 372), (440, 362), (464, 384), (462, 412), (430, 420), (408, 400)]}
BEIGE = {"armchair", "column"}  # mismo color que el piso: no se les borra el piso del borde
SURE = 7     # píxeles que se achica el polígono para marcar mueble seguro
MARGIN = 3   # píxeles que se agranda el polígono: más allá es fondo seguro


def cut_mask(img, poly, keep_floor=False):
    h, w = img.shape[:2]
    inside = np.zeros((h, w), np.uint8)
    cv2.fillPoly(inside, [np.array(poly, np.int32)], 1)
    grown = cv2.dilate(inside, np.ones((2 * MARGIN + 1,) * 2, np.uint8))
    sure = cv2.erode(inside, np.ones((2 * SURE + 1,) * 2, np.uint8))
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    mask[grown > 0] = cv2.GC_PR_BGD
    mask[inside > 0] = cv2.GC_PR_FGD
    mask[sure > 0] = cv2.GC_FGD
    x, y, bw, bh = cv2.boundingRect(np.array(poly, np.int32))
    x0, y0 = max(0, x - 30), max(0, y - 30)
    x1, y1 = min(w, x + bw + 30), min(h, y + bh + 30)
    sub = mask[y0:y1, x0:x1].copy()
    cv2.grabCut(img[y0:y1, x0:x1], sub, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    mask[y0:y1, x0:x1] = sub
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    # una sola pieza, sin agujeros chicos
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=4)
    if n > 1:
        fg = (lab == 1 + int(stats[1:, cv2.CC_STAT_AREA].argmax())).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) & (grown > 0)
    return fg if keep_floor else drop_floor(img, fg)


def floor_like(img):
    """Baldosas, juntas y alfombra (beige y azul grisáceo)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    beige = (h >= 8) & (h <= 26) & (s >= 30) & (s <= 125) & (v >= 140)
    rug = (h >= 100) & (h <= 135) & (s >= 25) & (s <= 110) & (v >= 60) & (v <= 140)
    return beige | rug


def drop_floor(img, fg):
    """Saca el piso que GrabCut dejó pegado: zonas con color de piso que tocan el borde del recorte.
    El contorno oscuro de cada mueble corta el relleno; lo de color de piso adentro del mueble queda."""
    region = (floor_like(img) & (fg > 0)).astype(np.uint8)
    edge = (fg > 0) & (cv2.dilate((fg == 0).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    n, lab = cv2.connectedComponents(region, connectivity=4)
    touching = np.unique(lab[edge & (region > 0)])
    out = fg.copy()
    out[np.isin(lab, touching[touching > 0])] = 0
    # descartar migas sueltas que quedaron del piso
    n, lab, stats, _ = cv2.connectedComponentsWithStats(out, connectivity=4)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 40:
            out[lab == i] = 0
    return out


def main():
    th = DIR / "theme.json"
    data = json.loads(th.read_text(encoding="utf-8"))
    scene = data["scene"]
    day = cv2.imread(str(DIR / "aligned" / "day.png"))
    images = {bg: cv2.imread(str(DIR / "aligned" / f"{bg}.png"), cv2.IMREAD_COLOR) for bg in BGS}
    only = sys.argv[1:]
    unknown = [n for n in only if n not in PIECES]
    if unknown:
        raise SystemExit(f"Muebles desconocidos: {unknown}")
    layers = {k: v for k, v in (scene.get("layers") or {}).items() if only and not k.startswith("_")}
    for name, (poly, foot) in PIECES.items():
        if only and name not in only:
            continue
        fg = cut_mask(day, poly, keep_floor=name in BEIGE)
        if name in KEEP:
            keep = np.zeros_like(fg)
            cv2.fillPoly(keep, [np.array(KEEP[name], np.int32)], 1)
            fg |= keep & cut_mask(day, poly, keep_floor=True)
        x, y, w, h = cv2.boundingRect(fg)
        for bg, img in images.items():
            out = DIR / "aligned" / "layers" / bg
            out.mkdir(parents=True, exist_ok=True)
            rgba = cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_BGR2BGRA)
            rgba[..., 3] = fg[y:y + h, x:x + w] * 255
            cv2.imwrite(str(out / f"{name}.png"), rgba)
        if foot.startswith("place:"):
            tiles = {str(scene["places"][foot[6:]]["tile"][0]): [[scene["places"][foot[6:]]["tile"][1]] * 2]}
        else:
            tiles = scene["footprints"][foot]
        layers[name] = {"pos": [x, y], "tiles": tiles}
        print(f"{name}: {w}x{h} en ({x}, {y}), {int(fg.sum())} píxeles")
    scene["layers"] = {"_comment": "Muebles recortados de cada fondo (aligned/layers/<fondo>/<mueble>.png, los genera "
                                   "cut_layers.py). pos = esquina en el fondo; tiles = huella en casillas. Se dibujan "
                                   "encima de los personajes que quedan detrás.", **layers}
    txt = json.dumps(data, indent=2, ensure_ascii=False)
    txt = re.sub(r'\[\s+(-?\d+(?:\.\d+)?),\s+(-?\d+(?:\.\d+)?)\s+\]', r'[\1, \2]', txt)
    txt = re.sub(r'\[\s+(\[[^\[\]]*\](?:,\s+\[[^\[\]]*\])*)\s+\]', lambda m: '[' + re.sub(r'\s+', ' ', m.group(1)) + ']', txt)
    th.write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
