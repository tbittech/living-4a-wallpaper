"""Convierte una hoja de animación de Gemini (N cuadros en fila sobre magenta) en cuadros nativos
y rearma el atlas del personaje.

Pasos: quitar el magenta, detectar la grilla de "píxeles falsos", reducir a la resolución nativa,
separar los cuadros, llevar los colores a la paleta de la hoja de referencia, limpiar píxeles sueltos,
alinear todos los cuadros por los pies y exportar.

Uso:
    python -I "Assets BBad/tools/extract_anim.py" HOJA.png PERSONAJE ANIMACION [--theme T]
        [--frames N] [--fps F] [--loop | --no-loop] [--keep-y] [--height F] [--pick 2,2,4,2] [--lower N] [--shift N] [--extra-colors N]

    python -I "Assets BBad/tools/extract_anim.py" --rebuild PERSONAJE   (solo rearma el atlas)

Cuadros, fps, loop, altura esperada (height, 1 = parado) y lower (dibujarla N píxeles más abajo)
salen de "animations" en theme.json; lower_by_character ({"leonard": 10}) lo cambia para un personaje.
shift / shift_by_character corre la animación en x (N píxeles a la derecha) para centrarla en el asiento.

Salida: themes/T/characters/PERSONAJE/
    anims/ANIMACION.png    tira de cuadros a resolución nativa
    anims/ANIMACION.json   cuadros, ancla de los pies, fps, loop, datos de la grilla
    anims/ANIMACION_x6.gif vista previa animada
    atlas.png + atlas.json todas las animaciones + las 4 vistas de referencia (ref_*)
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as themes  # noqa: E402
from extract_sheet import (VIEWS, edge_profile, fit_grid, grid_phase, magenta_mask,  # noqa: E402
                           quantize, sample_grid, save_png, split_views)

# Diferencia de color (Lab) por debajo de la cual un color se reemplaza por el de la referencia
SNAP_DE = 18.0


def read_rgba(path):
    return cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)


def to_lab(rgb):
    return cv2.cvtColor(rgb.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)


def tallest_frame(fg, count):
    """Altura en píxeles de la hoja del cuadro más alto (cada cuadro por separado:
    no están todos a la misma altura en la hoja)."""
    heights = []
    for x0, x1 in split_frames(fg, count):
        ys = np.nonzero(fg[:, x0:x1].any(axis=1))[0]
        heights.append(ys.max() - ys.min() + 1)
    return max(heights)


def detect_grid(img, fg, ref_height, count):
    """Grilla de la hoja. Si la altura nativa resultante no coincide con la referencia,
    se fuerza el tamaño de celda que la iguala (los cuadros quedan a la misma escala)."""
    prof_x = edge_profile(img, fg, axis=1)
    prof_y = edge_profile(img, fg, axis=0)
    sx, _, _ = fit_grid(prof_x)
    sy, _, _ = fit_grid(prof_y)
    s = max(sx, sy)
    if abs(sx - sy) / s > 0.02:
        print(f"  celdas distintas por eje ({sx:.2f} / {sy:.2f}), uso {s:.2f}")
    tallest_px = tallest_frame(fg, count)
    native_h = tallest_px / s
    mismatch = abs(native_h - ref_height) / ref_height
    print(f"  celda detectada {s:.3f} px -> altura nativa {native_h:.1f} (referencia {ref_height})")
    forced = False
    if mismatch > 0.08:
        s = tallest_px / ref_height
        forced = True
        print(f"  ATENCION: no coincide con la referencia ({mismatch:.0%}); fuerzo celda {s:.3f}. "
              "Revisar el resultado: si el generador dibujó a otra resolución, conviene regenerar la hoja.")
    px, qx = grid_phase(prof_x, s)
    py, qy = grid_phase(prof_y, s)
    print(f"  fase x {px:.2f} (calidad {qx:.2f})  fase y {py:.2f} (calidad {qy:.2f})")
    return s, px, py, forced, min(qx, qy)


def snap_palette(rgba, ref_colors, extra):
    """K-means para limpiar el ruido y después cada color al más cercano de la referencia.
    Los que quedan lejos (ropa nueva, objetos) se conservan como colores extra."""
    opaque = rgba[..., 3] > 0
    k = min(len(ref_colors) + extra, len(np.unique(rgba[..., :3][opaque], axis=0)))
    q = quantize(rgba, k)
    centers = np.unique(q[..., :3][opaque], axis=0)
    ref_lab = to_lab(ref_colors)
    # Tonos magenta que no están en la referencia: borde contaminado por el fondo, nunca color nuevo
    hsv = cv2.cvtColor(centers.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    tinted = (np.abs(hsv[:, 0].astype(int) - 150) < 22) & (hsv[:, 1] > 80)
    mapping, kept = {}, 0
    for c, lab, tint in zip(centers, to_lab(centers), tinted):
        d = np.linalg.norm(ref_lab - lab, axis=1)
        if d.min() < SNAP_DE or tint:
            mapping[tuple(c)] = ref_colors[int(d.argmin())]
        else:
            mapping[tuple(c)] = c
            kept += 1
    out = q.copy()
    flat = out.reshape(-1, 4)
    for i in np.nonzero(opaque.ravel())[0]:
        flat[i, :3] = mapping[tuple(flat[i, :3])]
    print(f"  paleta: {len(centers)} colores, {len(centers) - kept} llevados a la referencia, {kept} nuevos")
    return out


def magenta_tinted(colors):
    """Colores con tono magenta saturado (contorno contaminado por el fondo de la hoja)."""
    hsv = cv2.cvtColor(np.asarray(colors).reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    return (np.abs(hsv[:, 0].astype(int) - 150) < 22) & (hsv[:, 1] > 80)


def clean(rgba):
    """Quita píxeles opacos sueltos y tapa agujeros de 1 píxel (vecindad de 4)."""
    a = rgba[..., 3] > 0
    p = np.pad(a, 1)
    n = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    out = rgba.copy()
    out[a & (n == 0)] = 0
    holes = np.argwhere(~a & (n == 4))
    for y, x in holes:
        neigh = [rgba[y + dy, x + dx] for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        out[y, x] = neigh[0] if all((neigh[0] == v).all() for v in neigh) else neigh[2]
    removed, filled = int((a & (n == 0)).sum()), len(holes)
    if removed or filled:
        print(f"  limpieza: {removed} píxeles sueltos, {filled} agujeros")
    return out


def drop_slivers(f, x0, x1, share=0.04):
    """Borra pedazos del cuadro vecino que quedaron en el corte: manchas chicas (menos de share del
    cuadro) que tocan el borde izquierdo o derecho. Modifica f."""
    import cv2
    a = (f[..., 3] > 0).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(a, connectivity=8)
    total = a.sum()
    gone = 0
    for k in range(1, n):
        x, _, w, _, area = stats[k]
        if area < share * total and (x <= x0 or x + w >= x1):
            f[lab == k] = 0
            gone += area
    if gone:
        print(f"  cuadro {x0}-{x1}: {gone} píxeles del vecino borrados")


def split_frames(nfg, count):
    try:
        return split_views(nfg, count)
    except SystemExit:
        # Cuadros pegados o con partes sueltas: cortes parejos
        w = nfg.shape[1]
        print(f"  no se separaron {count} cuadros por columnas vacías; corto en partes iguales")
        return [[round(i * w / count), round((i + 1) * w / count)] for i in range(count)]


def feet_x(frame):
    """Centro horizontal de las piernas (último cuarto de la altura): ancla estable
    aunque los brazos se estiren."""
    a = frame[..., 3] > 0
    h = a.shape[0]
    _, xs = np.nonzero(a[int(h * 0.75):])
    return float(xs.mean())


def place_frames(frames, keep_y):
    """Mismo lienzo para todos, con el ancla de los pies en el mismo punto."""
    cuts = []
    for f, top, bottom in frames:
        _, xs = np.nonzero(f[..., 3])
        body = f[top:bottom, xs.min():xs.max() + 1]
        cuts.append((body, feet_x(body), bottom))
    left = max(int(np.ceil(fx)) for _, fx, _ in cuts) + 1
    right = max(int(np.ceil(c.shape[1] - fx)) for c, fx, _ in cuts) + 1
    W = left + right
    if keep_y:
        # Saltos y caídas: se respeta la altura relativa a la línea de piso común (la más baja)
        ground = max(b for *_, b in cuts)
        lift = [ground - b for *_, b in cuts]
    else:
        lift = [0] * len(cuts)
    H = max(c.shape[0] + l for (c, _, _), l in zip(cuts, lift)) + 2
    out = []
    for (body, fx, _), l in zip(cuts, lift):
        canvas = np.zeros((H, W, 4), np.uint8)
        x = left - int(round(fx))
        y = H - 1 - l - body.shape[0]
        canvas[y:y + body.shape[0], x:x + body.shape[1]] = body
        out.append(canvas)
    return out, (int(left), int(H - 1))


def gif_preview(path, frames, fps, scale=6):
    imgs = []
    for f in frames:
        big = cv2.resize(f, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        a = big[..., 3:4] / 255.0
        rgb = (big[..., :3] * a + 96 * (1 - a)).astype(np.uint8)
        imgs.append(Image.fromarray(rgb))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0, disposal=2)


def extract(args, th):
    char_dir = th.character(args.character)
    meta = json.loads((char_dir / "meta.json").read_text(encoding="utf-8"))
    ref_sheet = read_rgba(char_dir / "sheet.png")
    ref_colors = np.unique(ref_sheet[..., :3][ref_sheet[..., 3] > 0], axis=0)
    # Si la hoja de referencia quedó con contorno teñido de magenta (Leonard), esos colores no valen
    # como destino: el borde se lleva al color oscuro más cercano que no sea magenta
    tinted_ref = magenta_tinted(ref_colors)
    if tinted_ref.any() and not tinted_ref.all():
        print(f"  referencia: descarto {int(tinted_ref.sum())} colores teñidos de magenta")
        ref_colors = ref_colors[~tinted_ref]
    ref_height = max(h for _, h in meta["sizes"].values())
    # Animaciones más bajas que el personaje parado (sentado, agachado): altura esperada relativa
    height = args.height or th.data.get("animations", {}).get(args.anim, {}).get("height", 1.0)
    ref_height = round(ref_height * height)

    n, fps, loop = th.animation(args.anim)
    n = args.frames or n
    fps = args.fps or fps
    loop = loop if args.loop is None else args.loop

    print(f"{args.sheet.name} -> {args.character}/{args.anim} ({n} cuadros, {fps} fps, loop={loop})")
    img = cv2.imread(str(args.sheet), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"No se pudo leer {args.sheet}")
    bg = magenta_mask(img)
    bg = cv2.morphologyEx(bg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    fg = ~bg

    s, px, py, forced, quality = detect_grid(img, fg, ref_height, n)
    native = sample_grid(img, bg, s, px, s, py)
    native = clean(snap_palette(native, ref_colors, args.extra_colors))

    frames = []
    for x0, x1 in split_frames(native[..., 3] > 0, n):
        f = np.zeros_like(native)
        f[:, x0:x1] = native[:, x0:x1]
        drop_slivers(f, x0, x1)
        ys, _ = np.nonzero(f[..., 3])
        frames.append((f, ys.min(), ys.max() + 1))
    placed, anchor = place_frames(frames, args.keep_y)
    # lower: píxeles que se dibuja más abajo que los pies (type: el teclado tiene que apoyar en el escritorio)
    # Por personaje: animations.<anim>.lower_by_character (Leonard dibuja el teclado más abajo); --lower pisa todo
    spec = th.data.get("animations", {}).get(args.anim, {})
    lower = spec.get("lower_by_character", {}).get(args.character.lower(), spec.get("lower", 0))
    if args.lower is not None:
        lower = args.lower
    # shift: píxeles que se dibuja a la derecha (negativo: a la izquierda), para centrar en el asiento;
    # por personaje con animations.<anim>.shift_by_character, --shift pisa todo
    shift = spec.get("shift_by_character", {}).get(args.character.lower(), spec.get("shift", 0))
    if args.shift is not None:
        shift = args.shift
    anchor = (anchor[0] - shift, anchor[1] - lower)
    if args.pick:
        # Cuadros elegidos de la hoja y su orden (1 = el primero), para descartar los que cambian de vista
        pick = [int(v) for v in args.pick.split(",")]
        placed = [placed[i - 1] for i in pick]
        n = len(pick)
    H, W = placed[0].shape[:2]

    anim_dir = char_dir / "anims"
    anim_dir.mkdir(exist_ok=True)
    save_png(anim_dir / f"{args.anim}.png", np.concatenate(placed, axis=1))
    gif_preview(anim_dir / f"{args.anim}_x6.gif", placed, fps)
    info = {
        "source": args.sheet.name,
        "frames": n, "fps": fps, "loop": loop,
        "frame_size": [W, H], "anchor": list(anchor),
        "cell": round(s, 3), "cell_forced": forced, "grid_quality": round(quality, 2),
        "keep_y": args.keep_y, "pick": args.pick, "lower": lower, "shift": shift,
    }
    (anim_dir / f"{args.anim}.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    heights = [int((p[..., 3] > 0).any(axis=1).sum()) for p in placed]
    print(f"  cuadros {W}x{H}, ancla {anchor}, alturas {heights} -> {anim_dir}")


def build_atlas(character, th):
    """Una fila por animación; primero las 4 vistas de referencia como ref_*."""
    char_dir = th.character(character)
    meta = json.loads((char_dir / "meta.json").read_text(encoding="utf-8"))
    W, H = meta["frame_size"]
    rows = [("ref_" + v, [read_rgba(char_dir / f"{v}.png")], {"fps": 1, "loop": True, "anchor": [W // 2, H - 1]})
            for v in VIEWS]
    for js in sorted((char_dir / "anims").glob("*.json")) if (char_dir / "anims").exists() else []:
        info = json.loads(js.read_text(encoding="utf-8"))
        strip = read_rgba(js.with_suffix(".png"))
        fw, _ = info["frame_size"]
        frames = [strip[:, i * fw:(i + 1) * fw] for i in range(info["frames"])]
        rows.append((js.stem, frames, info))

    width = max(sum(f.shape[1] for f in fr) for _, fr, _ in rows)
    height = sum(fr[0].shape[0] for _, fr, _ in rows)
    atlas = np.zeros((height, width, 4), np.uint8)
    out = {"image": "atlas.png", "scale": th.sprite_scale, "animations": {}}
    y = 0
    for name, frames, info in rows:
        x, rects = 0, []
        for f in frames:
            h, w = f.shape[:2]
            atlas[y:y + h, x:x + w] = f
            rects.append([x, y, w, h])
            x += w
        out["animations"][name] = {"fps": info["fps"], "loop": info["loop"],
                                   "anchor": info["anchor"], "frames": rects}
        y += frames[0].shape[0]
    save_png(char_dir / "atlas.png", atlas)
    (char_dir / "atlas.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"atlas {width}x{height}: {', '.join(out['animations'])} -> {char_dir / 'atlas.png'}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("args", nargs="+", help="HOJA PERSONAJE ANIMACION, o PERSONAJE con --rebuild")
    ap.add_argument("--rebuild", action="store_true", help="solo rearmar atlas.png/atlas.json")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--fps", type=int)
    ap.add_argument("--loop", dest="loop", action="store_true", default=None)
    ap.add_argument("--no-loop", dest="loop", action="store_false")
    ap.add_argument("--keep-y", action="store_true", help="respetar saltos/caídas en vez de apoyar cada cuadro en el piso")
    ap.add_argument("--pick", help="cuadros de la hoja a usar y en qué orden, por ejemplo 2,2,4,2")
    ap.add_argument("--height", type=float, help="altura esperada respecto del personaje parado (sit ~0.8)")
    ap.add_argument("--lower", type=int, help="dibujarla N píxeles más abajo que los pies (pisa animations.lower del tema)")
    ap.add_argument("--shift", type=int, help="dibujarla N píxeles a la derecha, negativo a la izquierda (pisa animations.shift del tema)")
    ap.add_argument("--extra-colors", type=int, default=8, help="colores nuevos permitidos fuera de la referencia")
    themes.add_arg(ap)
    a = ap.parse_args()
    th = themes.load(a.theme)

    if a.rebuild:
        build_atlas(a.args[0], th)
        return
    if len(a.args) != 3:
        ap.error("se espera HOJA PERSONAJE ANIMACION")
    a.sheet, a.character, a.anim = Path(a.args[0]), a.args[1], a.args[2]
    extract(a, th)
    build_atlas(a.character, th)


if __name__ == "__main__":
    main()
