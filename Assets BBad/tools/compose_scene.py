"""Compone una escena de prueba: fondo alineado + personajes en los lugares del tema.

Sirve para revisar la zona caminable, los lugares y la escala de los sprites
antes de generar las hojas de animación.

Uso:
    python -I "Assets BBad/tools/compose_scene.py" walter@lab_table jesse@read:three_quarter:left
        [--theme T] [--bg day|night_idle|night_active] [--scale N] [--debug] [--out ARCHIVO.png]

Cada personaje es NOMBRE@LUGAR[:VISTA][:left]. LUGAR puede ser un lugar del tema (lab_table),
un rol genérico (shell, read, rest...) o coordenadas "x,y". VISTA puede ser una vista de referencia
o una animación ya extraída (sit, idle...: se usa su primer cuadro). Por defecto three_quarter
(o la que corresponde a la dirección del lugar, en temas con grilla); ":left" lo espeja.
Salida: el PNG a tamaño completo (por defecto themes/T/test_scene.png) y una copia a la mitad.
--effects pinta los efectos por código del tema (scene.effects, ver effects.py) en el instante --time;
el rol de cada personaje sale de LUGAR si es un rol (sheldon@shell) o de la animación (sheldon@desk:type).
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layers  # noqa: E402
import theme as themes  # noqa: E402
from grid import facings_of  # noqa: E402


def parse_actor(spec, th, taken):
    name, _, rest = spec.partition("@")
    parts = rest.split(":")
    where, view, flip = parts[0], "three_quarter", False
    role = where if where in th.data.get("roles", {}) else None
    if "," not in where:
        # Grupo de asientos (couch, desk) -> el del personaje o el primero libre
        where = th.place_key(where, name.lower(), taken)
        taken.add(where)
    facing = None if "," in where else th.facing(where)
    if facing:
        _, view, flip = facings_of(th.scene)[facing]
    for p in parts[1:]:
        if p == "left":
            flip = True
        elif p:
            view = p
    if "," in where:
        x, y = (int(v) for v in where.split(","))
        tile = th.grid.tile_at(x, y) if th.grid else None
    else:
        x, y = th.place(where)
        p = th.scene["places"][where]
        tile = tuple(p["tile"]) if isinstance(p, dict) else None
    return {"name": name, "view": view, "flip": flip, "x": x, "y": y, "tile": tile, "place": where, "role": role}


def effect_state(th, actors):
    """{lugar: rol} de los personajes, para los efectos (pantallas, pizarrón...)."""
    roles = {k: v for k, v in th.data.get("roles", {}).items() if isinstance(v, dict)}
    seats = th.scene.get("seats", {})
    state = {}
    for a in actors:
        role = a["role"]
        if role is None:
            # Sin rol explícito: el rol cuyo lugar (o grupo de asientos) y animación coinciden
            for k, r in roles.items():
                group = seats.get(r.get("place"))
                here = r.get("place") == a["place"] or (isinstance(group, list) and a["place"] in group)
                if here and r.get("anim") == a["view"]:
                    role = k
                    break
        if role:
            state[a["place"]] = role
    return state


def draw_debug(img, th):
    scene = th.scene
    d = ImageDraw.Draw(img, "RGBA")
    grid = th.grid
    if grid:
        for a, b in grid.walkable:
            d.polygon(grid.polygon(a, b), fill=(0, 255, 255, 40), outline=(0, 200, 200, 200))
    if scene.get("walkable"):
        poly = [tuple(p) for p in scene["walkable"]]
        d.polygon(poly, fill=(0, 255, 255, 50), outline=(0, 255, 255, 255))
    for name, pt in (scene.get("places") or {}).items():
        if pt is None:
            continue
        if isinstance(pt, dict):
            d.polygon(grid.polygon(*pt["tile"]), outline=(255, 0, 255, 255))
            pt = grid.center(*pt["tile"])
        x, y = pt
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 0, 255, 255))
        d.text((x + 8, y + 4), name, fill=(255, 255, 0, 255))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("actors", nargs="*")
    themes.add_arg(ap)
    ap.add_argument("--bg", default="day")
    ap.add_argument("--scale", type=int)
    ap.add_argument("--debug", action="store_true", help="dibuja la zona caminable y los lugares")
    ap.add_argument("--effects", action="store_true", help="pinta los efectos por código del tema (scene.effects)")
    ap.add_argument("--time", type=float, default=1.0, help="instante de los efectos, en segundos")
    ap.add_argument("--out")
    args = ap.parse_args()

    th = themes.load(args.theme)
    scale = args.scale or th.sprite_scale
    bg_path = th.aligned / f"{args.bg}.png"
    if not bg_path.exists():
        raise SystemExit(f"Falta {bg_path}: correr align_backgrounds.py --theme {th.name}")
    img = layers.background(th, args.bg) if th.grid else Image.open(bg_path).convert("RGBA")
    if args.debug:
        draw_debug(img, th)

    taken = set()
    actors = [parse_actor(a, th, taken) for a in args.actors]
    for a in actors:
        char = th.character(a["name"])
        anim = char / "anims" / f"{a['view']}.png"
        if anim.exists():
            # Una animación (sit, idle...): su primer cuadro, anclado por los pies
            meta = json.loads(anim.with_suffix(".json").read_text(encoding="utf-8"))
            w, h = meta["frame_size"]
            spr = Image.open(anim).convert("RGBA").crop((0, 0, w, h))
            ax, ay = meta["anchor"]
        else:
            # Vista de referencia. Ancla: centro de la base del lienzo (los pies están en la última fila)
            spr = Image.open(char / f"{a['view']}.png").convert("RGBA")
            ax, ay = spr.width // 2, spr.height
        if a["flip"]:
            spr, ax = spr.transpose(Image.FLIP_LEFT_RIGHT), spr.width - 1 - ax
        a["sprite"] = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
        a["pos"] = (a["x"] - ax * scale, a["y"] - ay * scale)
    if th.grid:
        # Grilla: muebles de primer plano encima de quien queda detrás
        fg = layers.load(th, args.bg)
        if args.effects:
            import effects
            fx, state = effects.Effects(th, args.bg), effect_state(th, actors)
            img, fg = fx.under(img, fg, args.time, state)
        layers.compose(img, fg, actors)
        if args.effects:
            fx.over(img, args.time, state)
    else:
        # Orden por Y de los pies: el que está más abajo se dibuja adelante
        for a in sorted(actors, key=lambda a: a["y"]):
            img.alpha_composite(a["sprite"], a["pos"])

    out = Path(args.out) if args.out else th.dir / "test_scene.png"
    img.convert("RGB").save(out)
    img.convert("RGB").resize((img.width // 2, img.height // 2), Image.NEAREST).save(
        out.with_name(out.stem + "_half.png"))
    print(f"{out}  (tema {th.name}, escala x{scale}, {len(actors)} personajes)")


if __name__ == "__main__":
    main()
