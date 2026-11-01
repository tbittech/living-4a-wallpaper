"""Alinea los fondos del tema a su imagen de referencia y los recorta a un tamaño común.

Los fondos, cuál es la referencia y la zona que tiene que quedar fija (align_box)
salen de theme.json del tema.

Uso:
    python -I "Assets BBad/tools/align_backgrounds.py" [--theme NOMBRE] [--debug DIR]

Salida: themes/NOMBRE/aligned/{estado}.png + alignment.json
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as themes  # noqa: E402

SRC = None  # carpeta backgrounds/ del tema (se fija en main)

# Rectángulo que más importa que no tiemble (la van, el living...), en fracciones
# del ancho/alto de la referencia. El ajuste fino se hace ahí. Sale de theme.json.
ALIGN_BOX = (0.0, 0.0, 1.0, 1.0)


def load(name):
    img = cv2.imread(str(SRC / name), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"No se pudo leer {SRC / name}")
    return img


def structure(img):
    """Imagen de bordes normalizada: sirve igual de día y de noche."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    return gray


def gradient(gray):
    g = cv2.GaussianBlur(gray, (0, 0), 2).astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    mag = cv2.magnitude(gx, gy)
    return mag / (mag.max() + 1e-6)


def box_mask(shape):
    h, w = shape[:2]
    x0, y0, x1, y1 = ALIGN_BOX
    mask = np.zeros((h, w), np.uint8)
    mask[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
    return mask


def coarse_fit(ref_gray, mov_gray):
    """SIFT + RANSAC con transformación de similitud (escala, rotación, traslación)."""
    sift = cv2.SIFT_create(nfeatures=20000)
    mask = box_mask(ref_gray.shape)
    kr, dr = sift.detectAndCompute(ref_gray, mask)
    km, dm = sift.detectAndCompute(mov_gray, None)
    matches = cv2.BFMatcher(cv2.NORM_L2).knnMatch(dm, dr, k=2)
    good = [m for m, n in (p for p in matches if len(p) == 2) if m.distance < 0.75 * n.distance]
    if len(good) < 12:
        raise SystemExit(f"Pocas coincidencias ({len(good)})")
    src = np.float32([km[m.queryIdx].pt for m in good])
    dst = np.float32([kr[m.trainIdx].pt for m in good])
    M, inliers = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                            ransacReprojThreshold=3.0, maxIters=20000)
    return M, int(inliers.sum()), len(good)


def refine(ref_gray, mov_gray, M):
    """ECC sobre los bordes, solo en la zona fija (align_box)."""
    ref_g = gradient(ref_gray)
    mov_g = gradient(mov_gray)
    warp = M.astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6)
    try:
        cc, warp = cv2.findTransformECC(ref_g, mov_g, warp, cv2.MOTION_AFFINE,
                                        criteria, box_mask(ref_gray.shape), 5)
    except cv2.error:
        return M, None
    return warp.astype(np.float64), float(cc)


def edge_score(ref_gray, warped_gray):
    """Correlación de bordes dentro de la zona fija (1 = idénticos)."""
    m = box_mask(ref_gray.shape) > 0
    a = gradient(ref_gray)[m]
    b = gradient(warped_gray)[m]
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def main():
    global SRC, ALIGN_BOX
    ap = argparse.ArgumentParser()
    themes.add_arg(ap)
    ap.add_argument("--debug", type=Path, help="carpeta para imágenes de control")
    args = ap.parse_args()

    th = themes.load(args.theme)
    cfg = th.data["backgrounds"]
    SRC, out_dir = th.backgrounds, th.aligned
    if cfg.get("align_box"):
        ALIGN_BOX = tuple(cfg["align_box"])
    ref_key = cfg["reference"]
    ref_name = cfg["sources"][ref_key]
    others = [(k, v) for k, v in cfg["sources"].items() if k != ref_key]
    print(f"tema {th.name}: referencia {ref_name}, zona fija {ALIGN_BOX}")

    ref = load(ref_name)
    h, w = ref.shape[:2]
    ref_gray = structure(ref)

    results = {ref_key: ref}
    valid = np.full((h, w), 255, np.uint8)
    report = {}

    for key, name in others:
        mov = load(name)
        mov_gray = structure(mov)
        M0, n_in, n_good = coarse_fit(ref_gray, mov_gray)
        before = edge_score(ref_gray, cv2.warpAffine(mov_gray, M0, (w, h)))
        M, cc = refine(ref_gray, mov_gray, M0)
        after = edge_score(ref_gray, cv2.warpAffine(mov_gray, M, (w, h)))
        if after < before:  # el refinamiento empeoró: quedarse con el ajuste grueso
            M, after = M0, before

        results[key] = cv2.warpAffine(mov, M, (w, h), flags=cv2.INTER_LANCZOS4,
                                      borderMode=cv2.BORDER_CONSTANT)
        cover = cv2.warpAffine(np.full(mov.shape[:2], 255, np.uint8), M, (w, h),
                               flags=cv2.INTER_NEAREST)
        valid &= cover

        scale = float(np.hypot(M[0, 0], M[1, 0]))
        angle = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        report[key] = {
            "source": name,
            "source_size": [mov.shape[1], mov.shape[0]],
            "matches": n_good, "inliers": n_in,
            "scale": round(scale, 5), "rotation_deg": round(angle, 4),
            "shift_px": [round(float(M[0, 2]), 2), round(float(M[1, 2]), 2)],
            "edge_corr_coarse": round(before, 4), "edge_corr_final": round(after, 4),
            "affine": np.round(M, 6).tolist(),
        }

        if args.debug:
            args.debug.mkdir(parents=True, exist_ok=True)
            wg = cv2.warpAffine(mov_gray, M, (w, h))
            # rojo = referencia, verde/azul = alineada: los bordes coinciden si se ven grises
            overlay = cv2.merge([wg, wg, ref_gray])
            cv2.imwrite(str(args.debug / f"overlay_{key}.jpg"), overlay)

    # Rectángulo más grande dentro de la zona válida, con un margen de seguridad.
    # Se achica el rectángulo desde el borde con más píxeles vacíos hasta que no quede ninguno.
    ok = valid > 0
    y0, y1, x0, x1 = 0, h, 0, w
    while True:
        sides = {
            "top": (~ok[y0, x0:x1]).sum(), "bottom": (~ok[y1 - 1, x0:x1]).sum(),
            "left": (~ok[y0:y1, x0]).sum(), "right": (~ok[y0:y1, x1 - 1]).sum(),
        }
        worst = max(sides, key=sides.get)
        if sides[worst] == 0:
            break
        if worst == "top": y0 += 1
        elif worst == "bottom": y1 -= 1
        elif worst == "left": x0 += 1
        else: x1 -= 1
    margin = 2
    x0, x1, y0, y1 = x0 + margin, x1 - margin, y0 + margin, y1 - margin
    # Ancho y alto pares, para escalar y codificar sin problemas.
    x1 -= (x1 - x0) % 2
    y1 -= (y1 - y0) % 2

    out_dir.mkdir(exist_ok=True)
    for key, img in results.items():
        cv2.imwrite(str(out_dir / f"{key}.png"), img[y0:y1, x0:x1])

    report["crop"] = {"x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0),
                      "reference": ref_name, "reference_size": [w, h]}
    (out_dir / "alignment.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
