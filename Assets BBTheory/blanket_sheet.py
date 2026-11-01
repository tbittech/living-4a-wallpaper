"""Sheldon con la manta y la notebook en el sillón: una hoja de 3×4 -> tres animaciones.

Fila 1 -> blanket_on (se pone la manta y saca la notebook, sin loop)
Fila 2 -> blanket_type (teclea encapuchado; loop, dura lo que haga falta)
Fila 3 -> blanket_off (cierra la notebook, la deja en el piso y se saca la manta, sin loop)

No sirve extract_anim.py tal cual: la notebook en el piso queda más abajo que los zapatos y la manta
cuelga hasta el piso, así que el "más bajo" y el centro de las piernas se corren de un cuadro a otro.
Acá el ancla sale de las canillas (píxeles caqui de abajo), calibrada contra anims/sit.png para que
el paso sit -> blanket_on no salte; la notebook puede quedar por debajo del ancla.

    python -I "Assets BBTheory/blanket_sheet.py" [HOJA]   (por defecto characters/sheldon/source/blanket.webp)
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "Assets BBad" / "tools"
sys.path.insert(0, str(TOOLS))
import theme as themes  # noqa: E402
from extract_anim import build_atlas, clean, gif_preview, read_rgba, snap_palette  # noqa: E402
from extract_sheet import edge_profile, fit_grid, grid_phase, magenta_mask, sample_grid, save_png  # noqa: E402

CHAR = "sheldon"
ROWS = [("blanket_on", 4, False), ("blanket_type", 6, True), ("blanket_off", 4, False)]
# Canillas: los últimos SHIN píxeles nativos de pantalón caqui
SHIN = 12
# Menos píxeles caqui que esto en las canillas: están tapadas (por la manta)
MIN_SHIN = 40


def khaki(rgba):
    """Pantalón caqui: los dos tonos claros (145,120,84 y 118,93,64). Los oscuros se repiten en el
    contorno, el pelo y la notebook; la piel es más clara."""
    hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return (rgba[..., 3] > 0) & (h >= 8) & (h <= 25) & (s > 60) & (s < 170) & (v >= 112) & (v < 175)


def shin_anchor(rgba):
    """(x, y) de las canillas: centro de los últimos SHIN renglones caqui y el más bajo."""
    ys, xs = np.nonzero(khaki(rgba))
    bottom = ys.max()
    sel = ys > bottom - SHIN
    return float(xs[sel].mean()), int(bottom)


def runs(a):
    out, s = [], None
    for i, v in enumerate(a):
        if v and s is None:
            s = i
        if not v and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(a)))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    th = themes.load("big_bang")
    char_dir = th.character(CHAR)
    sheet = Path(sys.argv[1]) if len(sys.argv) > 1 else char_dir / "source" / "blanket.webp"
    img = cv2.imread(str(sheet), cv2.IMREAD_COLOR)
    bg = magenta_mask(img)
    bg = cv2.morphologyEx(bg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    fg = ~bg

    # Una sola grilla para toda la hoja (las tres filas son del mismo dibujo). Viene a ~2 px por píxel,
    # debajo del mínimo de fit_grid (4): se busca entre 1.5 y 4
    prof_x, prof_y = edge_profile(img, fg, axis=1), edge_profile(img, fg, axis=0)
    s = max(fit_grid(prof_x, 1.5, 4.0)[0], fit_grid(prof_y, 1.5, 4.0)[0])
    px, py = grid_phase(prof_x, s)[0], grid_phase(prof_y, s)[0]
    print(f"{sheet.name}: celda {s:.3f} px")
    native = sample_grid(img, bg, s, px, s, py)
    ref = read_rgba(char_dir / "sheet.png")
    ref_colors = np.unique(ref[..., :3][ref[..., 3] > 0], axis=0)
    # Colores nuevos: manta (3-4 tonos), notebook roja, resplandor de la pantalla
    native = clean(snap_palette(native, ref_colors, 16))

    # Calibración contra sit: dónde caen sus canillas respecto de su ancla
    sit = json.loads((char_dir / "anims" / "sit.json").read_text(encoding="utf-8"))
    sit_strip = read_rgba(char_dir / "anims" / "sit.png")
    sx, sy = shin_anchor(sit_strip[:, :sit["frame_size"][0]])
    dx, dy = sit["anchor"][0] - sx, sit["anchor"][1] - sy

    # Celdas: filas y columnas separadas por magenta en la hoja (en píxeles nativos)
    nfg = native[..., 3] > 0
    row_runs = [r for r in runs(nfg.sum(axis=1) > 0) if r[1] - r[0] > 20]
    if len(row_runs) != 3:
        raise SystemExit(f"se esperaban 3 filas, hay {len(row_runs)}")
    for (name, fps, loop), (y0, y1) in zip(ROWS, row_runs):
        band = native[y0:y1]
        col_runs = [c for c in runs((band[..., 3] > 0).sum(axis=0) > 0) if c[1] - c[0] > 10]
        if len(col_runs) != 4:
            raise SystemExit(f"{name}: se esperaban 4 cuadros, hay {len(col_runs)}")
        # Ancla de cada cuadro en coordenadas de su celda de la hoja (4 celdas parejas por fila). Si la manta
        # tapa las canillas (blanket_on 2), la mediana del resto de la fila: el generador ubica al personaje
        # casi igual en cada celda (±4 px)
        cw = native.shape[1] / 4
        found = []
        for k, (x0, x1) in enumerate(col_runs):
            f = band[:, x0:x1]
            m = khaki(f)
            ok = m[m.any(axis=1).nonzero()[0].max() - SHIN + 1:].sum() >= MIN_SHIN
            ax, ay = shin_anchor(f)
            found.append((ax + x0 - k * cw, ay) if ok else None)
        known = [a for a in found if a]
        median = (float(np.median([a[0] for a in known])), int(np.median([a[1] for a in known])))
        cuts = []
        for k, ((x0, x1), a) in enumerate(zip(col_runs, found)):
            if a is None:
                print(f"  {name} {k + 1}: sin canillas a la vista, ancla de la mediana de la fila")
            ax, ay = a or median
            cuts.append((band[:, x0:x1], ax - x0 + k * cw + dx, ay + dy))
        # Mismo lienzo para los 4, con el ancla en el mismo punto (la notebook puede quedar debajo)
        left = int(np.ceil(max(ax for _, ax, _ in cuts))) + 1
        right = int(np.ceil(max(f.shape[1] - ax for f, ax, _ in cuts))) + 1
        top = int(np.ceil(max(ay for _, _, ay in cuts)))
        below = int(np.ceil(max(f.shape[0] - ay for f, _, ay in cuts)))
        W, H = left + right, top + below + 1
        placed = []
        for f, ax, ay in cuts:
            c = np.zeros((H, W, 4), np.uint8)
            x, y = left - int(round(ax)), top - int(round(ay))
            c[y:y + f.shape[0], x:x + f.shape[1]] = f
            placed.append(c)
        # Recorte de filas y columnas vacías comunes a los 4 cuadros
        any_a = np.any([p[..., 3] > 0 for p in placed], axis=0)
        ys, xs = np.nonzero(any_a)
        yt, xl = ys.min(), xs.min()
        placed = [p[yt:ys.max() + 1, xl:xs.max() + 1] for p in placed]
        anchor = [left - int(xl), top - int(yt)]
        H, W = placed[0].shape[:2]
        save_png(char_dir / "anims" / f"{name}.png", np.concatenate(placed, axis=1))
        gif_preview(char_dir / "anims" / f"{name}_x6.gif", placed, fps)
        info = {"source": sheet.name, "frames": 4, "fps": fps, "loop": loop, "frame_size": [W, H],
                "anchor": anchor, "cell": round(s, 3), "cell_forced": False, "grid_quality": None,
                "keep_y": False, "pick": None, "lower": 0, "shift": 0, "script": "blanket_sheet.py"}
        (char_dir / "anims" / f"{name}.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        print(f"  {name}: {W}x{H}, ancla {anchor}")
    build_atlas(CHAR, th)


if __name__ == "__main__":
    main()
