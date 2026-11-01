"""GIF de prueba: un personaje camina por la grilla del tema de un lugar a otro.

Sirve para revisar walk / walk_back sobre el fondo antes de tener el frontend:
camino más corto casilla por casilla, vista y espejado según la dirección de cada paso.

Uso:
    python -I "Assets BBad/tools/walk_preview.py" Sheldon door couch --theme big_bang
        [--bg day] [--speed 2.5] [--fps 15] [--anim type] [--out ARCHIVO.gif]

DESDE y HASTA pueden ser lugares, roles o grupos de asientos (couch, desk), como en compose_scene.py.
Al llegar reproduce sit (asientos) o idle; si falta una animación se usa la vista de referencia quieta.
--effects suma los efectos por código del tema (scene.effects, ver effects.py); los que dependen de un rol
(pantallas, pizarrón) arrancan al llegar: el rol es HASTA si es un rol (shell, edit...) o el de --anim.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layers  # noqa: E402
import theme as themes  # noqa: E402
from grid import FACINGS, facing_of  # noqa: E402

# Dirección -> animación de caminar (las de la izquierda son las de la derecha espejadas)
WALK = {"three_quarter": "walk", "back": "walk_back"}


def load_anim(char_dir, name, scale):
    """Cuadros de una animación ya escalados y su ancla (pies), o None si no existe."""
    path = char_dir / "anims" / f"{name}.png"
    if not path.exists():
        return None
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    strip = Image.open(path).convert("RGBA")
    w, h = meta["frame_size"]
    frames = [strip.crop((i * w, 0, (i + 1) * w, h)).resize((w * scale, h * scale), Image.NEAREST)
              for i in range(meta["frames"])]
    ax, ay = meta["anchor"]
    return frames, (ax * scale, ay * scale), meta["fps"]


def load_still(char_dir, view, scale):
    """Vista de referencia quieta (ancla: centro de la base)."""
    im = Image.open(char_dir / f"{view}.png").convert("RGBA")
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return [im], (im.width // 2, im.height - 1), 1


def walk_anims(char_dir, scale, names=WALK):
    """Animación de caminar (o correr) por vista; la vista quieta si falta."""
    return {view: load_anim(char_dir, name, scale) or load_still(char_dir, view, scale) for view, name in names.items()}


def walk_steps(g, start, path, anims, fps, speed, t0=0):
    """Cuadros de caminar casilla por casilla: [(sprite, pos, casilla para tapar)]."""
    out = []
    per_tile = max(1, round(fps / speed))
    t, cur = t0, start
    for nxt in path:
        _, view, flip = FACINGS[facing_of((nxt[0] - cur[0], nxt[1] - cur[1]))]
        frames, (ax, ay), afps = anims[view]
        (x0, y0), (x1, y1) = g.center(*cur), g.center(*nxt)
        for i in range(per_tile):
            k = (i + 1) / per_tile
            x, y = round(x0 + (x1 - x0) * k), round(y0 + (y1 - y0) * k)
            spr = frames[int(t / fps * afps) % len(frames)]
            if flip:
                spr, axx = spr.transpose(Image.FLIP_LEFT_RIGHT), spr.width - 1 - ax
            else:
                axx = ax
            # Para tapar se usa la casilla más cercana a la cámara de las dos del paso
            out.append((spr, (x - axx, y - ay), (max(cur[0], nxt[0]), max(cur[1], nxt[1]))))
            t += 1
        cur = nxt
    return out


def hold(anim, flip, x, y, tile, seconds, fps):
    """Cuadros de quedarse en un lugar reproduciendo una animación (pies en x, y)."""
    frames, (ax, ay), afps = anim
    if flip:
        frames, ax = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in frames], frames[0].width - 1 - ax
    return [(frames[int(i / fps * afps) % len(frames)], (x - ax, y - ay), tile) for i in range(round(seconds * fps))]


def ghost(spr, strength):
    """Clon de la estela: difuminado, teñido hacia rojo/amarillo y con transparencia."""
    g = spr.filter(ImageFilter.GaussianBlur(1.2))
    r, gr, b, a = g.split()
    tint = Image.merge("RGBA", (r.point(lambda v: min(255, v + 60)), gr.point(lambda v: min(255, v + 25)),
                                b.point(lambda v: v // 2), a.point(lambda v: int(v * strength))))
    return tint


def with_trail(steps, length=6):
    """Agrega a cada cuadro los clones de los cuadros anteriores: [[(sprite, pos, casilla), ...]].
    El primero de cada lista es el personaje; los demás, la estela (más vieja, más transparente)."""
    out = []
    for i, step in enumerate(steps):
        actors = [step]
        for k in range(1, length + 1):
            if i - k < 0:
                break
            spr, pos, tile = steps[i - k]
            if pos == step[1]:
                continue
            actors.append((ghost(spr, 0.55 * (1 - k / (length + 1))), pos, tile))
        out.append(actors)
    return out


def save_gif(path, frames, fps):
    """GIF, o MP4 si path termina en .mp4 (escenas largas: pesa mucho menos)."""
    path = Path(path)
    if path.suffix == ".mp4":
        import cv2
        import numpy as np
        w, h = frames[0].size
        vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        for f in frames:
            vw.write(cv2.cvtColor(np.asarray(f.convert("RGB")), cv2.COLOR_RGB2BGR))
        vw.release()
        return
    rgb = [f.convert("RGB") for f in frames]
    rgb[0].save(path, save_all=True, append_images=rgb[1:], duration=round(1000 / fps), loop=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("start")
    ap.add_argument("goal")
    themes.add_arg(ap)
    ap.add_argument("--bg", default="day")
    ap.add_argument("--speed", type=float, default=2.5, help="casillas por segundo")
    ap.add_argument("--fps", type=int, default=15, help="cuadros por segundo del GIF")
    ap.add_argument("--anim", help="animación al llegar (type, write...); por defecto sit en un asiento o idle")
    ap.add_argument("--effects", action="store_true", help="pinta los efectos por código del tema (scene.effects)")
    ap.add_argument("--out")
    args = ap.parse_args()

    th = themes.load(args.theme)
    g = th.grid
    if g is None:
        raise SystemExit(f"El tema '{th.name}' no tiene grilla de casillas")
    who = args.character.lower()
    places = th.scene["places"]
    start_key = th.place_key(args.start, who)
    goal_key = th.place_key(args.goal, who, taken={start_key})
    start, goal = tuple(places[start_key]["tile"]), tuple(places[goal_key]["tile"])
    path = g.path(start, goal)
    if path is None:
        raise SystemExit(f"No hay camino de {start_key} {start} a {goal_key} {goal}")
    print(f"{args.character}: {start_key} {start} -> {goal_key} {goal}, {len(path)} pasos")

    scale = th.sprite_scale
    char_dir = th.character(args.character)
    anims = walk_anims(char_dir, scale)
    bg = layers.background(th, args.bg)
    fg_layers = layers.load(th, args.bg)

    steps = walk_steps(g, start, path, anims, args.fps, args.speed)
    # Al llegar, tres segundos: sit en un asiento, idle parado (son de 3/4 de frente);
    # si falta la animación o el lugar mira de espaldas, la vista quieta
    _, view, flip = FACINGS[places[goal_key]["facing"]]
    seated = any(goal_key in seats for seats in th.scene.get("seats", {}).values() if isinstance(seats, list))
    if args.anim:
        arrive = load_anim(char_dir, args.anim, scale)
    else:
        arrive = load_anim(char_dir, "sit" if seated else "idle", scale) if view == "three_quarter" else None
    arrived = len(steps)
    steps += hold(arrive or load_still(char_dir, view, scale), flip, *th.place(goal_key), goal, 3, args.fps)

    if args.effects:
        import effects
        fx = effects.Effects(th, args.bg)
        roles = {k: v for k, v in th.data.get("roles", {}).items() if isinstance(v, dict)}
        role = args.goal if args.goal in roles else next(
            (k for k, r in roles.items() if args.anim and r.get("anim") == args.anim), None)
        out_frames = []
        for i, (s_, p, t) in enumerate(steps):
            sec = i / args.fps
            state = {goal_key: {"role": role, "since": arrived / args.fps}} if role and i >= arrived else {}
            img, fg = fx.under(bg, fg_layers, sec, state)
            layers.compose(img, fg, [{"sprite": s_, "pos": p, "tile": t}])
            out_frames.append(fx.over(img, sec, state))
    else:
        out_frames = [layers.compose(bg.copy(), fg_layers, [{"sprite": s_, "pos": p, "tile": t}])
                      for s_, p, t in steps]
    out = Path(args.out) if args.out else th.dir / f"walk_{who}.gif"
    save_gif(out, out_frames, args.fps)
    print(f"{out}  ({len(out_frames)} cuadros a {args.fps} fps)")


if __name__ == "__main__":
    main()
