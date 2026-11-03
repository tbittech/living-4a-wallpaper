"""Exporta un tema al bundle que lee el frontend del wallpaper (ver WALLPAPER.md §2).

theme.json + fondos + capas + props + atlas de los personajes -> wallpaper/public/bundle/<tema>/
    bundle.json                   grilla, casillas, lugares, asientos, roles, capas, personajes
    bg/<fondo>.png                fondo alineado con los props pintados (layers.background)
    layers/<fondo>/<nombre>.png   muebles recortados y props con la luz de cada fondo (layers.load)
    chars/<id>/atlas.png          atlas de cada personaje (id en minúscula)
    fx/<fondo>/<efecto>.png       lo precalculado de los efectos por código (effects.py: _prep_*)
    _ref/<escena>.png             escenas de referencia hechas con Python, para comparar con ?ref=<escena>

Los puntos donde van los pies (centro de cada casilla y de cada lugar) salen precalculados de Python,
así el frontend redondea igual que compose_scene.py / walk_preview.py. De los efectos se exporta lo que
calcula _prep_* (formas, máscaras, píxeles de tinta, luces); el frontend porta solo los _draw_*.
Correr desde E:\\ProyectosIA:  python -I wallpaper/export_bundle.py [--theme big_bang]
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "Assets BBad" / "tools"))
import effects  # noqa: E402
import layers  # noqa: E402
import theme as themes  # noqa: E402
from grid import facings_of  # noqa: E402

BGS = ("day", "night_idle", "night_active")
# Escenas de referencia: theme.json -> "refs": [{"name", "bg", "t", "actors": [[id, lugar, animación]], "state"}]
# (cuadro 0 de cada animación; state = estado de los efectos)

def save_alpha(shape, path):
    """Forma en [0, 1] -> PNG blanco con esa forma en el alfa."""
    a = np.clip(np.round(shape * 255), 0, 255).astype(np.uint8)
    rgba = np.dstack([np.full_like(a, 255)] * 3 + [a])
    Image.fromarray(rgba, "RGBA").save(path)


def export_effects(th, out):
    """Configuración de scene.effects y, por fondo, lo que precalcula cada efecto."""
    cfg = th.scene.get("effects") or {}
    data = {}
    px = 2
    for bg in BGS:
        fx = effects.Effects(th, bg)
        px = fx.px
        folder = out / "fx" / bg
        folder.mkdir(parents=True)
        d = {}
        for name, e in fx.items:
            c = fx.cache.get(name)
            kind = e["type"]
            if kind in ("glow", "spill"):
                save_alpha(c["shape"], folder / f"{name}.png")
                d[name] = {"box": [int(v) for v in c["box"]], "img": f"fx/{bg}/{name}.png"}
            elif kind == "board":
                d[name] = {"xs": c["xs"].tolist(), "ys": c["ys"].tolist(), "white": [float(v) for v in c["white"]]}
            elif kind == "clouds":
                save_alpha(c["sky"].astype(float), folder / f"{name}.png")
                d[name] = {"box": list(c["box"]), "img": f"fx/{bg}/{name}.png", "s": c["s"], "clouds": [
                    {"cells": sorted([xx, yy, int(yy == cl["bottom"][xx])] for xx, yy in cl["cells"]),
                     "y": cl["y"], "span": list(cl["span"]), "x": cl["x"], "speed": cl["speed"]}
                    for cl in c["clouds"]]}
            elif kind == "lights":
                d[name] = {"comps": [{"px": np.column_stack([comp["idx"][1], comp["idx"][0]]).ravel().tolist(),
                                      "dark": [float(v) for v in comp["dark"]]} for comp in c["comps"]],
                           "extra": [list(p) for p in c["extra"]]}
            elif kind == "sprite":
                s = c["s"]
                blocks = []
                for left, top, light in c["places"]:
                    for j, row in enumerate(c["rows"]):
                        for i, ch in enumerate(row):
                            if ch in c["pal"]:
                                col = np.clip(np.asarray(c["pal"][ch], float) * light, 0, 255)
                                blocks.append([int(left + i * s), int(top + j * s), s] + [float(v) for v in col])
                d[name] = {"blocks": blocks}
            elif kind == "steam":
                sources = [list(p) for p in e.get("sources", [])]
                if e.get("from"):
                    sources += [[int(x), int(y)] for x, y in fx.sprite_tops(e["from"])]
                d[name] = {"sources": sources}
            else:
                d[name] = {}
        data[bg] = d
    config = {k: v for k, v in cfg.items() if isinstance(v, dict) and not k.startswith("_")}
    return {"px": px, "config": config, "data": data}


def export_refs(th, out, chars):
    """Escenas de referencia compuestas con el pipeline de Python (layers + effects)."""
    (out / "_ref").mkdir()
    refs = []
    sc = th.sprite_scale
    for ref in th.data.get("refs", []):
        bg = ref["bg"]
        actors = []
        for cid, place, anim in ref["actors"]:
            meta = json.loads((th.character(chars[cid]) / "atlas.json").read_text(encoding="utf-8"))
            atlas = Image.open(th.character(chars[cid]) / meta["image"]).convert("RGBA")
            a = meta["animations"][anim]
            x, y, w, h = a["frames"][0]
            spr = atlas.crop((x, y, x + w, y + h))
            ax, ay = a["anchor"]
            if sc != 1:
                spr, ax, ay = spr.resize((w * sc, h * sc), Image.NEAREST), ax * sc, ay * sc
            if facings_of(th.scene)[th.scene["places"][place]["facing"]][2]:
                spr, ax = spr.transpose(Image.FLIP_LEFT_RIGHT), spr.width - 1 - ax
            fx_, fy = th.place(place)
            actors.append({"sprite": spr, "pos": (fx_ - ax, fy - ay), "tile": tuple(th.scene["places"][place]["tile"])})
        fx = effects.Effects(th, bg)
        img, fg = fx.under(layers.background(th, bg), layers.load(th, bg), ref["t"], ref["state"])
        layers.compose(img, fg, actors)
        fx.over(img, ref["t"], ref["state"])
        img.convert("RGB").save(out / "_ref" / f"{ref['name']}.png")
        refs.append(dict(ref, img=f"_ref/{ref['name']}.png"))
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=json.loads((ROOT / "public" / "config.json").read_text(encoding="utf-8"))["theme"])
    args = ap.parse_args()

    th = themes.load(args.theme)
    g = th.grid
    if g is None:
        raise SystemExit(f"El tema '{th.name}' no tiene grilla de casillas")
    sc = th.scene
    out = ROOT / "public" / "bundle" / th.name
    if out.exists():
        shutil.rmtree(out)
    (out / "bg").mkdir(parents=True)

    # Fondos y capas (mismo orden que layers.load: muebles y después props)
    size = None
    layer_meta = []
    for bg in BGS:
        img = layers.background(th, bg)
        size = img.size
        img.save(out / "bg" / f"{bg}.png")
        (out / "layers" / bg).mkdir(parents=True)
        for i, l in enumerate(layers.load(th, bg)):
            l["img"].save(out / "layers" / bg / f"{l['name']}.png")
            if bg == BGS[0]:
                layer_meta.append({"name": l["name"], "pos": list(l["pos"]), "size": list(l["img"].size),
                                   "tiles": sorted(list(t) for t in l["tiles"]), "depth": l["depth"]})

    # Lugares: casilla, dirección y los pies ya calculados (con offset)
    places = {}
    for key, p in sc["places"].items():
        if not isinstance(p, dict):
            continue
        places[key] = {"tile": p["tile"], "facing": p["facing"], "foot": list(th.place(key))}
    walkable = sorted([a, b] for a, b in g.walkable)
    # Pies en el centro de cada casilla: las caminables y las de los lugares (asientos fuera del piso)
    centers = {f"{a},{b}": list(g.center(a, b)) for a, b in walkable}
    for p in places.values():
        centers.setdefault(f"{p['tile'][0]},{p['tile'][1]}", list(g.center(*p["tile"])))

    # Personajes: los que tienen atlas
    chars = {}
    folders = {}
    for d in sorted(th.characters.iterdir()):
        atlas = d / "atlas.json"
        if not atlas.exists():
            continue
        cid = d.name.lower()
        meta = json.loads(atlas.read_text(encoding="utf-8"))
        (out / "chars" / cid).mkdir(parents=True)
        s = th.sprite_scale
        anims = meta["animations"]
        if s == 1:
            shutil.copy(d / meta["image"], out / "chars" / cid / "atlas.png")
        else:
            # El frontend dibuja los sprites a tamaño nativo: el atlas sale ya agrandado (sin suavizar).
            # Ancla escalada igual que compose_scene.py (esquina del bloque), para que ?ref=...&diff=1 coincida.
            img = Image.open(d / meta["image"])
            img.resize((img.width * s, img.height * s), Image.NEAREST).save(out / "chars" / cid / "atlas.png")
            anims = {k: dict(a, frames=[[v * s for v in f] for f in a["frames"]],
                             anchor=[v * s for v in a["anchor"]])
                     for k, a in anims.items()}
        chars[cid] = {"atlas": f"chars/{cid}/atlas.png", "anims": anims}
        folders[cid] = d.name

    bundle = {
        "theme": th.name,
        "size": list(size),
        "sprite_scale": th.sprite_scale,
        "grid": sc["grid"],
        "walkable": walkable,
        "centers": centers,
        "places": places,
        "facings": {k: {"step": list(d), "view": v, "flip": f} for k, (d, v, f) in g.facings.items()},
        "seats": {k: v for k, v in sc.get("seats", {}).items() if isinstance(v, list)},
        "owners": sc.get("owners", {}),
        "prefers": {k: v for k, v in sc.get("prefers", {}).items() if not k.startswith("_")},
        "only": {k: v for k, v in sc.get("only", {}).items() if not k.startswith("_")},
        "roles": {k: v for k, v in th.data.get("roles", {}).items() if isinstance(v, dict)},
        "cast": {k: v for k, v in th.data.get("cast", {}).items() if not k.startswith("_")},
        "animations": {k: v for k, v in th.data.get("animations", {}).items() if isinstance(v, dict)},
        "backgrounds": list(BGS),
        "layers": layer_meta,
        "characters": chars,
        "effects": export_effects(th, out),
        "refs": export_refs(th, out, folders),
    }
    (out / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{out}: {len(walkable)} casillas, {len(places)} lugares, {len(layer_meta)} capas, "
          f"personajes {', '.join(chars)}")


if __name__ == "__main__":
    main()
