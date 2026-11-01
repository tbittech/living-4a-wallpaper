"""Convierte una hoja de referencia de Gemini (4 vistas sobre magenta) en sprites nativos.

Detecta la grilla de "píxeles falsos", reduce cada vista a su resolución real,
quita el magenta y deja las 4 vistas del mismo tamaño, alineadas por los pies.

Uso:
    python -I "Assets BBad/tools/extract_sheet.py" HOJA.jpg NOMBRE [--theme T] [--colors N]
        [--order front,three_quarter,back,side] [--height 110]   (orden de las vistas en la hoja, de izquierda a derecha)

Salida: themes/T/characters/NOMBRE/
    source/HOJA.jpg                                    (copia de la hoja, si estaba en otro lado)
    front.png, three_quarter.png, side.png, back.png   (resolución nativa, con transparencia)
    sheet.png                                          (las 4 vistas juntas)
    preview_x6.png                                     (vista previa ampliada sobre gris)
    meta.json
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as themes  # noqa: E402

VIEWS = ["front", "three_quarter", "side", "back"]


def magenta_mask(img):
    """True donde hay fondo magenta (tolerante a JPEG)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1], hsv[..., 2]
    # Magenta en OpenCV: tono ~150 (0-180)
    return (np.abs(h - 150) < 14) & (s > 120) & (v > 150)


def split_views(fg, count):
    """Separa las vistas por columnas vacías. Devuelve [(x0, x1)]."""
    cols = fg.sum(axis=0) > 2
    runs, start = [], None
    for x, on in enumerate(cols):
        if on and start is None:
            start = x
        elif not on and start is not None:
            runs.append([start, x])
            start = None
    if start is not None:
        runs.append([start, len(cols)])
    # Unir huecos chicos (por ejemplo, entre una oreja y la cabeza)
    while len(runs) > count:
        gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
        i = int(np.argmin(gaps))
        runs[i][1] = runs[i + 1][1]
        del runs[i + 1]
    if len(runs) != count:
        raise SystemExit(f"Se esperaban {count} vistas y se encontraron {len(runs)}")
    return runs


def edge_profile(img, fg, axis):
    """Energía de cambios de color a lo largo de un eje, solo sobre el personaje."""
    f = img.astype(np.float32)
    if axis == 1:
        d = np.abs(np.diff(f, axis=1)).sum(axis=2)
        m = fg[:, 1:] & fg[:, :-1]
        return (d * m).sum(axis=0)
    d = np.abs(np.diff(f, axis=0)).sum(axis=2)
    m = fg[1:, :] & fg[:-1, :]
    return (d * m).sum(axis=1)


def fit_grid(profile, lo=4.0, hi=48.0):
    """Tamaño de celda y fase de la grilla a partir de dónde caen los bordes.

    Cada borde está entre i e i+1. Para cada tamaño candidato se suman los bordes
    como fasores; la grilla real los alinea. s/2 puntúa igual que s, así que entre
    los candidatos casi máximos se queda con el más grande.
    """
    pos = np.arange(len(profile)) + 1.0
    w = profile / (profile.sum() + 1e-9)
    sizes = np.arange(lo, hi, 0.02)
    scores = np.array([abs((w * np.exp(-2j * np.pi * pos / s)).sum()) for s in sizes])
    good = sizes[scores >= 0.92 * scores.max()]
    s = float(good.max())
    # Refinar alrededor del elegido
    fine = np.arange(s - 0.3, s + 0.3, 0.002)
    fs = np.array([abs((w * np.exp(-2j * np.pi * pos / f)).sum()) for f in fine])
    s = float(fine[int(np.argmax(fs))])
    return s, *grid_phase(profile, s)


def grid_phase(profile, s):
    pos = np.arange(len(profile)) + 1.0
    w = profile / (profile.sum() + 1e-9)
    z = (w * np.exp(-2j * np.pi * pos / s)).sum()
    phase = (np.angle(z) / (2 * np.pi) * s) % s
    return float(phase), float(abs(z))


def sample_grid(img, bg, sx, px, sy, py):
    """Un color por celda: mediana del centro de la celda; transparente si es fondo."""
    h, w = bg.shape
    xs = np.arange(px, w, sx)
    ys = np.arange(py, h, sy)
    out = np.zeros((len(ys) - 1, len(xs) - 1, 4), np.uint8)
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        cy0, cy1 = int(y0 + 0.3 * sy), int(np.ceil(y1 - 0.3 * sy))
        for i in range(len(xs) - 1):
            x0, x1 = xs[i], xs[i + 1]
            cx0, cx1 = int(x0 + 0.3 * sx), int(np.ceil(x1 - 0.3 * sx))
            cell_bg = bg[cy0:cy1, cx0:cx1]
            if cell_bg.size == 0 or cell_bg.mean() > 0.5:
                continue
            px_ = img[cy0:cy1, cx0:cx1][~cell_bg]
            b, g, r = np.median(px_, axis=0)
            out[j, i] = (r, g, b, 255)
    return out


def quantize(rgba, colors):
    """Reduce la paleta para limpiar el ruido de JPEG (k-means sobre los opacos)."""
    opaque = rgba[..., 3] > 0
    data = rgba[..., :3][opaque].astype(np.float32)
    k = min(colors, len(np.unique(data, axis=0)))
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, labels, centers = cv2.kmeans(data, k, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    out = rgba.copy()
    out[..., :3][opaque] = centers[labels.ravel()].round().astype(np.uint8)
    return out


def defringe(rgba):
    """Colores con tono magenta (borde contaminado por el fondo) -> el color no magenta más parecido."""
    opaque = rgba[..., 3] > 0
    colors = np.unique(rgba[..., :3][opaque], axis=0)
    hsv = cv2.cvtColor(colors.reshape(-1, 1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    tinted = (np.abs(hsv[:, 0].astype(int) - 150) < 22) & (hsv[:, 1] > 80)
    clean = colors[~tinted].astype(int)
    if not tinted.any() or not len(clean):
        return rgba
    out = rgba.copy()
    for c in colors[tinted]:
        near = clean[np.abs(clean - c.astype(int)).sum(axis=1).argmin()]
        out[opaque & (rgba[..., :3] == c).all(axis=2), :3] = near
    return out


def trim(rgba):
    ys, xs = np.nonzero(rgba[..., 3])
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def save_png(path, rgba):
    cv2.imwrite(str(path), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", type=Path)
    ap.add_argument("name")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--height", type=int,
                    help="altura nativa de las figuras; fuerza la celda (para igualar a otro personaje, p. ej. 110)")
    ap.add_argument("--order", default=",".join(VIEWS),
                    help="orden de las vistas en la hoja, separado por comas")
    themes.add_arg(ap)
    args = ap.parse_args()
    order = args.order.split(",")
    if sorted(order) != sorted(VIEWS):
        raise SystemExit(f"--order tiene que ser una permutación de {','.join(VIEWS)}")
    out_dir = themes.load(args.theme).character(args.name)

    img = cv2.imread(str(args.sheet), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"No se pudo leer {args.sheet}")
    bg = magenta_mask(img)
    bg = cv2.morphologyEx(bg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    fg = ~bg

    prof_x = edge_profile(img, fg, axis=1)
    prof_y = edge_profile(img, fg, axis=0)
    sx, px, qx = fit_grid(prof_x)
    sy, py, qy = fit_grid(prof_y)
    # Los píxeles son cuadrados: si un eje encontró una fracción de la celda (s/2, s/3),
    # se usa la celda del otro eje y solo se recalcula la fase.
    s = max(sx, sy)
    if abs(sx - sy) / s > 0.02:
        sx = sy = s
        px, qx = grid_phase(prof_x, s)
        py, qy = grid_phase(prof_y, s)
    if args.height:
        ys = np.nonzero(fg.any(axis=1))[0]
        s = (ys[-1] - ys[0] + 1) / args.height
        print(f"altura forzada a {args.height}: celda {sx:.3f} -> {s:.3f}")
        sx = sy = s
        px, qx = grid_phase(prof_x, s)
        py, qy = grid_phase(prof_y, s)
    print(f"grilla x: celda {sx:.3f} fase {px:.2f} (calidad {qx:.2f})")
    print(f"grilla y: celda {sy:.3f} fase {py:.2f} (calidad {qy:.2f})")

    native = sample_grid(img, bg, sx, px, sy, py)
    native = defringe(quantize(native, args.colors))

    nfg = native[..., 3] > 0
    found = {}
    for name, (x0, x1) in zip(order, split_views(nfg, len(VIEWS))):
        v = np.zeros_like(native)
        v[:, x0:x1] = native[:, x0:x1]
        found[name] = trim(v)
    views = [found[n] for n in VIEWS]

    # Mismo lienzo para las 4, centradas y con los pies en la misma línea
    W = max(v.shape[1] for v in views) + 2
    H = max(v.shape[0] for v in views) + 2
    src_dir = out_dir / "source"
    src_dir.mkdir(parents=True, exist_ok=True)
    if args.sheet.resolve().parent != src_dir.resolve():
        shutil.copy2(args.sheet, src_dir / args.sheet.name)
    frames = []
    for name, v in zip(VIEWS, views):
        canvas = np.zeros((H, W, 4), np.uint8)
        x = (W - v.shape[1]) // 2
        canvas[H - 1 - v.shape[0]:H - 1, x:x + v.shape[1]] = v
        save_png(out_dir / f"{name}.png", canvas)
        frames.append(canvas)

    sheet = np.concatenate(frames, axis=1)
    save_png(out_dir / "sheet.png", sheet)

    scale = 6
    big = cv2.resize(sheet, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    preview = np.full(big.shape[:2] + (3,), 96, np.uint8)
    a = big[..., 3:4] / 255.0
    preview = (big[..., :3] * a + preview * (1 - a)).astype(np.uint8)
    cv2.imwrite(str(out_dir / "preview_x6.png"), cv2.cvtColor(preview, cv2.COLOR_RGB2BGR))

    meta = {
        "source": args.sheet.name,
        "cell": [round(sx, 3), round(sy, 3)],
        "phase": [round(px, 2), round(py, 2)],
        "frame_size": [W, H],
        "views": VIEWS,
        "sizes": {n: [v.shape[1], v.shape[0]] for n, v in zip(VIEWS, views)},
        "colors": args.colors,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"vistas: {meta['sizes']}  lienzo {W}x{H}  -> {out_dir}")


if __name__ == "__main__":
    main()
