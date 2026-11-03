"""Efectos por código del escenario: cosas que se mueven en el fondo sin ser personajes.

theme.json -> scene.effects: {"px": 2, "nombre": {"type": ..., ...}, ...}
Todo en píxeles del fondo alineado. Tipos:

    glow     resplandor que parpadea (la tele de noche): elipse isométrica en bandas duras con
             tramado, color e intensidad que cambian a saltos. "behind": capas que lo tapan.
    board    ecuaciones que se van escribiendo en un objeto agregado (scene.props): mientras el rol
             está activo se borra la tinta del dibujo original y se vuelve a escribir en orden de renglón.
    clouds   nubes de bloques que cruzan las ventanas (solo sobre los píxeles de cielo).
    lights   luces de la ciudad por la ventana: las luces del fondo titilan y se prenden y apagan
             ventanitas extra en los edificios.
    sprite   dibujito de bloques definido en el json (las cajas de comida china), con la luz del fondo.
    steam    vapor que sube en bloques desde puntos o desde las cajas de un "sprite".
    screen   pantalla de compu prendida mientras el rol está en su lugar: de frente, líneas de código
             que suben (rect); de espaldas, un filo de luz (rim).
    spill    reflejo de una pantalla sobre quien la mira (va con stage over).
    tumbleweed  planta rodadora que cruza una franja del piso cada tanto (every, chance), rodando y rebotando.

Claves comunes: "backgrounds" (fondos donde va; todos si falta), "role" / "place" (solo cuando hay
alguien con ese rol, en ese lugar), "stage": "under" (debajo de capas y personajes) u "over" (encima).

Uso:
    fx = effects.Effects(th, "night_active")
    bg, fg = fx.under(bg, fg_layers, t, state)      # fondo y capas con los efectos de abajo
    layers.compose(bg, fg, actores)
    fx.over(bg, t, state)                            # vapor, reflejos
state: {lugar: rol} o {lugar: {"role": rol, "since": t0}} (since: cuándo empezó, para el pizarrón).
"""
import math
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import layers as layermod

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16


def rnd(*key):
    """Número fijo en [0, 1) para una clave (mismo resultado en cada corrida)."""
    return (zlib.crc32(repr(key).encode()) & 0xFFFFFF) / 0x1000000


def steps(t, seed, lo, hi):
    """Índice del tramo de tiempo en el que cae t: tramos de largo al azar entre lo y hi.

    El tiempo se parte en bloques de largo hi y cada bloque en 1..hi/lo tramos iguales
    (cantidad al azar por bloque): parpadeos irregulares, sin tener que recorrer desde 0."""
    b = int(t // hi)
    cuts = 1 + int(rnd(seed, "cuts", b) * max(1, round(hi / lo)))
    return b * 1000 + int((t - b * hi) / (hi / cuts))


def norm_state(state):
    out = {}
    for place, v in (state or {}).items():
        if isinstance(v, dict):
            out[place] = (v.get("role"), v.get("since", 0.0))
        else:
            out[place] = (v, 0.0)
    return out


def _listify(v):
    return [v] if isinstance(v, str) else list(v or [])


class Effects:
    def __init__(self, th, bg):
        self.th, self.bg = th, bg
        cfg = th.scene.get("effects") or {}
        self.px = int(cfg.get("px", 2))
        self.items = [(k, v) for k, v in cfg.items()
                      if isinstance(v, dict) and not k.startswith("_")
                      and (not v.get("backgrounds") or bg in v["backgrounds"])]
        self.base = layermod.background(th, bg)
        self.W, self.H = self.base.size
        self.rgb = np.asarray(self.base.convert("RGB"), float)
        self.layer_specs = layermod.load(th, bg)
        self.cache = {}
        for name, e in self.items:
            prep = getattr(self, f"_prep_{e['type']}", None)
            if prep:
                self.cache[name] = prep(name, e)

    # ---- estado -----------------------------------------------------------------------------
    def active(self, e, state):
        """None si el efecto no corre; si corre, desde cuándo (t0)."""
        roles, places = _listify(e.get("role")), _listify(e.get("place"))
        if not roles and not places:
            return 0.0
        hits = [since for place, (role, since) in state.items()
                if (not roles or role in roles) and (not places or place in places)]
        return min(hits) if hits else None

    # ---- aplicar ----------------------------------------------------------------------------
    def _overlay(self, stage, t, state):
        st = norm_state(state)
        ov = np.zeros((self.H, self.W, 4), float)   # color premultiplicado + alfa
        for name, e in self.items:
            if e.get("stage", "over" if e["type"] == "steam" else "under") != stage:
                continue
            t0 = self.active(e, st)
            if t0 is None:
                continue
            getattr(self, f"_draw_{e['type']}")(ov, name, e, t, t - t0)
        if not ov[..., 3].any():
            return None
        a = ov[..., 3:4]
        rgb = np.where(a > 0, ov[..., :3] / np.maximum(a, 1e-6), 0)
        return Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), "RGBA")

    def under(self, bg_img, fg_layers, t, state):
        """Fondo y capas con los efectos de abajo (devuelve copias)."""
        ov = self._overlay("under", t, state)
        if ov is None:
            return bg_img.copy(), fg_layers
        out = bg_img.copy()
        out.alpha_composite(ov)
        box = ov.getbbox()
        new = []
        for l in fg_layers:
            x, y = l["pos"]
            lb = (x, y, x + l["img"].width, y + l["img"].height)
            if box and lb[0] < box[2] and box[0] < lb[2] and lb[1] < box[3] and box[1] < lb[3]:
                piece = ov.crop(lb)
                pa = np.asarray(piece).copy()
                pa[..., 3] = (pa[..., 3].astype(int) * (np.asarray(l["img"].getchannel("A")) > 0)).astype(np.uint8)
                img = l["img"].copy()
                img.alpha_composite(Image.fromarray(pa, "RGBA"))
                l = dict(l, img=img)
            new.append(l)
        return out, new

    def over(self, frame, t, state):
        """Efectos de arriba (vapor, reflejos) sobre el cuadro ya compuesto. Modifica frame."""
        ov = self._overlay("over", t, state)
        if ov is not None:
            frame.alpha_composite(ov)
        return frame

    # ---- utilidades de dibujo ---------------------------------------------------------------
    def _blend(self, ov, mask, color, alpha, box=None):
        """Pinta color con alfa (escalar o matriz) donde mask (bool); box: recorte (x0, y0, x1, y1)
        al que corresponden mask y alpha, para no recorrer la imagen entera."""
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H)
        sl = ov[y0:y1, x0:x1]
        a = np.where(mask, alpha, 0.0)
        keep = 1 - a
        sl[..., :3] = sl[..., :3] * keep[..., None] + np.asarray(color, float) * a[..., None]
        sl[..., 3] = sl[..., 3] * keep + a

    def _paint(self, ov, ys, xs, color, alpha):
        """Pinta píxeles sueltos (índices) con color y alfa."""
        ov[ys, xs, :3] = ov[ys, xs, :3] * (1 - alpha) + np.asarray(color, float) * alpha
        ov[ys, xs, 3] = ov[ys, xs, 3] * (1 - alpha) + alpha

    def _box_fill(self, ov, box, color, alpha):
        x0, y0, x1, y1 = box
        self._blend(ov, np.ones((y1 - y0, x1 - x0), bool), color, alpha, box)

    def _block(self, ov, x, y, color, alpha=1.0, size=None):
        s = size or self.px
        x, y = int(x) // s * s, int(y) // s * s
        if x < 0 or y < 0 or x + s > self.W or y + s > self.H:
            return
        sl = ov[y:y + s, x:x + s]
        sl[..., :3] = sl[..., :3] * (1 - alpha) + np.asarray(color, float) * alpha
        sl[..., 3] = sl[..., 3] * (1 - alpha) + alpha

    def _layer_mask(self, names):
        m = np.zeros((self.H, self.W), bool)
        for l in self.layer_specs:
            if l["name"] in names:
                x, y = l["pos"]
                a = np.asarray(l["img"].getchannel("A")) > 0
                h, w = a.shape
                m[y:y + h, x:x + w] |= a[:max(0, min(h, self.H - y)), :max(0, min(w, self.W - x))]
        return m

    def _light(self, box):
        """Cuánto se oscurece o tiñe el fondo bg en box respecto del de día (como los props)."""
        if self.bg == "day":
            return np.ones(3)
        day = np.asarray(Image.open(self.th.aligned / "day.png").convert("RGB").crop(box), float).mean(axis=(0, 1))
        now = self.rgb[box[1]:box[3], box[0]:box[2]].mean(axis=(0, 1))
        return now / np.maximum(day, 1)

    def _iso_glow(self, center, radius, bands):
        """Alfa en bandas duras y tramadas de una elipse con radios (rx, ry): (matriz, recorte)."""
        cx, cy = center
        rx, ry = radius
        s = self.px
        box = (max(0, (cx - rx) // s * s), max(0, (cy - ry) // s * s),
               min(self.W, cx + rx + s), min(self.H, cy + ry + s))
        ys, xs = np.mgrid[box[1]:box[3], box[0]:box[2]]
        bx, by = xs // s, ys // s
        d = np.sqrt(((bx * s - cx) / rx) ** 2 + ((by * s - cy) / ry) ** 2)
        v = np.clip(1 - d, 0, 1)
        q = np.floor(v * bands + BAYER[by % 4, bx % 4] * 0.999) / bands   # bandas con tramado
        return q, box

    # ---- glow: la tele --------------------------------------------------------------------
    def _prep_glow(self, name, e):
        shape, box = self._iso_glow(e["center"], e["radius"], e.get("bands", 3))
        if e.get("behind"):
            shape[self._layer_mask(set(e["behind"]))[box[1]:box[3], box[0]:box[2]]] = 0
        return {"shape": shape, "box": box}

    def _draw_glow(self, ov, name, e, t, since):
        lo, hi = e.get("flicker", [0.1, 0.4])
        i = steps(t, name, lo, hi)
        levels = e.get("alpha", [0.1, 0.2, 0.3])
        level = levels[int(rnd(name, "lvl", i) * len(levels))]
        colors = e.get("colors", [[200, 220, 255]])
        scene = int(t / e.get("scene_s", 1.6))     # el color cambia por "escena" de la tele
        color = colors[int(rnd(name, "col", scene) * len(colors))]
        c = self.cache[name]
        self._blend(ov, c["shape"] > 0, color, c["shape"] * level * 2, c["box"])
        if e.get("rim"):
            self._box_fill(ov, e["rim"], color, min(1.0, level * 2.5))

    # ---- board: el pizarrón ---------------------------------------------------------------
    def _prep_board(self, name, e):
        spec = self.th.scene["props"][e["prop"]]
        img = layermod._prop(self.th, spec, self.bg)
        a = np.asarray(img, float)
        mask_img = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask_img).polygon([tuple(p) for p in e["polygon"]], fill=255)
        mask_img = mask_img.filter(ImageFilter.MinFilter(3))       # sin el marco
        inside = (np.asarray(mask_img) > 0) & (a[..., 3] > 0)
        lum = a[..., :3].mean(axis=2)
        white = np.median(a[inside & (lum >= np.percentile(lum[inside], 60))][:, :3], axis=0)
        ink = inside & (lum < white.mean() * e.get("ink_below", 0.82))
        ys, xs = np.nonzero(ink)
        # Orden de escritura: renglones paralelos al borde de arriba del pizarrón, de izquierda a derecha
        (x0, y0), (x1, y1) = e["polygon"][0], e["polygon"][1]
        slope = (y1 - y0) / max(1, x1 - x0)
        line = np.floor((ys - y0 - slope * (xs - x0)) / e.get("line_h", 6)).astype(int)
        order = np.lexsort((xs, line))
        px, py = spec["pos"]
        return {"xs": xs[order] + px, "ys": ys[order] + py, "white": white,
                "ink": a[ys[order], xs[order], :3]}

    def _draw_board(self, ov, name, e, t, since):
        c = self.cache[name]
        n = len(c["xs"])
        write, hold, erase = e.get("write_s", 8), e.get("hold_s", 2), e.get("erase_s", 0.8)
        f = since % (write + hold + erase)
        if f < write:
            # Va escribiendo: a saltos (trazos), no pixel por pixel parejo
            shown = int(n * math.floor(f / write * 40) / 40)
            hidden = slice(shown, n)
        elif f < write + hold:
            hidden = slice(n, n)
        else:
            # Borrado de izquierda a derecha
            k = (f - write - hold) / erase
            xs = c["xs"]
            cut = xs.min() + (xs.max() - xs.min() + 1) * k
            idx = xs < cut
            ov[c["ys"][idx], xs[idx], :3] = c["white"]
            ov[c["ys"][idx], xs[idx], 3] = 1
            return
        ys, xs = c["ys"][hidden], c["xs"][hidden]
        ov[ys, xs, :3] = c["white"]
        ov[ys, xs, 3] = 1
        # Punta del marcador en el último trazo
        if f < write and 0 < hidden.start < n:
            i = hidden.start - 1
            ov[c["ys"][i], c["xs"][i], :3] = e.get("marker", [40, 60, 160])
            ov[c["ys"][i], c["xs"][i], 3] = 1

    # ---- clouds: nubes de día -------------------------------------------------------------
    def _sky_mask(self, rects, rule):
        m = np.zeros((self.H, self.W), bool)
        r, g, b = self.rgb[..., 0], self.rgb[..., 1], self.rgb[..., 2]
        sky = (g - r >= rule.get("g_minus_r", 12)) & (b - r >= rule.get("b_minus_r", 12)) & \
              ((r + g + b) / 3 >= rule.get("min_lum", 170))
        for x0, y0, x1, y1 in rects:
            m[y0:y1, x0:x1] = sky[y0:y1, x0:x1]
        return m

    def _prep_clouds(self, name, e):
        rects = e["rects"]
        sky = self._sky_mask(rects, e.get("sky", {}))
        s = e.get("block", 3)
        x0 = min(r[0] for r in rects)
        x1 = max(r[2] for r in rects)
        y0 = min(r[1] for r in rects)
        y1 = max(r[3] for r in rects)
        clouds = []
        for k in range(e.get("count", 4)):
            w = e.get("min_w", 8) + int(rnd(name, k, "w") * e.get("var_w", 8))   # en bloques
            h = e.get("min_h", 3) + int(rnd(name, k, "h") * 2)
            cells = set()
            for j in range(3):                            # unión de 3 rectángulos redondeados
                cw = max(3, int(w * (0.5 + 0.5 * rnd(name, k, j, "cw"))))
                cx = int((w - cw) * rnd(name, k, j, "cx"))
                ch = h + (1 if j == 1 else 0)
                for yy in range(ch):
                    for xx in range(cw):
                        if (yy == 0 or yy == ch - 1) and xx in (0, cw - 1):
                            continue
                        cells.add((cx + xx, h + 1 - ch + yy))
            bottom = {}
            for xx, yy in cells:
                bottom[xx] = max(bottom.get(xx, -1), yy)
            # Cada nube cruza una ventana (se reparten) por la mitad de arriba, que es cielo
            rx0, ry0, rx1, ry1 = rects[k % len(rects)]
            clouds.append({"cells": cells, "bottom": bottom, "w": w,
                           "y": (ry0 + int((ry1 - ry0) * 0.45 * rnd(name, k, "y"))) // s * s,
                           "span": (rx0 - (w + 1) * s, rx1 + s),
                           "x": rnd(name, k, "x"), "speed": e.get("speed", 4) * (0.7 + 0.6 * rnd(name, k, "v"))})
        return {"sky": sky[y0:y1, x0:x1], "box": (x0, y0, x1, y1), "clouds": clouds, "s": s}

    def _draw_clouds(self, ov, name, e, t, since):
        c = self.cache[name]
        s = c["s"]
        colors = e.get("colors", [[255, 255, 255], [220, 234, 240]])
        bx0, by0, bx1, by1 = c["box"]
        cloud_layer = np.zeros((by1 - by0, bx1 - bx0, 4), float)
        for cl in c["clouds"]:
            lo, hi = cl["span"]
            x = lo + ((cl["x"] * (hi - lo) + t * cl["speed"]) % (hi - lo))
            x = int(x) // s * s
            for xx, yy in cl["cells"]:
                col = colors[1] if yy == cl["bottom"][xx] else colors[0]
                X, Y = x + xx * s - bx0, cl["y"] + yy * s - by0
                if 0 <= X and X + s <= bx1 - bx0 and 0 <= Y and Y + s <= by1 - by0:
                    cloud_layer[Y:Y + s, X:X + s, :3] = col
                    cloud_layer[Y:Y + s, X:X + s, 3] = e.get("alpha", 0.9)
        m = c["sky"] & (cloud_layer[..., 3] > 0)
        sl = ov[by0:by1, bx0:bx1]
        a = cloud_layer[m, 3:4]
        sl[m, :3] = cloud_layer[m, :3] * a
        sl[m, 3] = a[:, 0]

    # ---- lights: luces de la ciudad -------------------------------------------------------
    def _prep_lights(self, name, e):
        import cv2
        rects = e["rects"]
        lum = self.rgb.mean(axis=2)
        r, g, b = self.rgb[..., 0], self.rgb[..., 1], self.rgb[..., 2]
        area = np.zeros((self.H, self.W), bool)
        for x0, y0, x1, y1 in rects:
            area[y0:y1, x0:x1] = True
        bright = area & (lum >= e.get("min_lum", 150))
        n, lab = cv2.connectedComponents(bright.astype(np.uint8), connectivity=8)
        comps = []
        for k in range(1, n):
            m = lab == k
            if m.sum() > e.get("max_size", 40):
                continue                                   # algo grande: no es una luz
            ring = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~bright
            dark = self.rgb[ring].mean(axis=0) if ring.any() else self.rgb[m].mean(axis=0) * 0.3
            comps.append({"idx": np.nonzero(m), "dark": dark})
        # Ventanitas extra sobre los edificios (píxeles oscuros y azulados)
        # Edificios: oscuros y casi grises (el cielo de noche es bastante más azul; el ladrillo, más rojo)
        building = area & (lum < e.get("building_max_lum", 75)) & (b >= r) & (b - r < e.get("building_max_blue", 20))
        s = self.px
        extra = []
        tries = 0
        while len(extra) < e.get("extra", 10) and tries < 4000:
            tries += 1
            x = int(rects[tries % len(rects)][0] + rnd(name, "x", tries) * (rects[tries % len(rects)][2] - rects[tries % len(rects)][0])) // s * s
            y = int(rects[tries % len(rects)][1] + rnd(name, "y", tries) * (rects[tries % len(rects)][3] - rects[tries % len(rects)][1])) // s * s
            if building[y - 1:y + s + 1, x - 1:x + s + 1].all() and all(abs(x - a) > 4 or abs(y - b_) > 4 for a, b_ in extra):
                extra.append((x, y))
        return {"comps": comps, "extra": extra}

    def _draw_lights(self, ov, name, e, t, since):
        c = self.cache[name]
        lo, hi = e.get("period", [0.5, 3.0])
        off = e.get("off_chance", 0.25)
        for k, comp in enumerate(c["comps"]):
            i = steps(t, (name, k), lo, hi)
            if rnd(name, k, i, "off") < off:
                # Apagada (o titilando): baja casi al color de alrededor
                self._paint(ov, *comp["idx"], comp["dark"], e.get("dim", 0.75))
        colors = e.get("colors", [[255, 214, 120]])
        for k, (x, y) in enumerate(c["extra"]):
            i = steps(t, (name, "x", k), lo * 2, hi * 2)
            if rnd(name, "x", k, i, "on") < e.get("on_chance", 0.55):
                self._block(ov, x, y, colors[int(rnd(name, "xc", k) * len(colors))])

    # ---- sprite: cajas de comida china ----------------------------------------------------
    def _prep_sprite(self, name, e):
        rows, pal = e["rows"], e["palette"]
        s = e.get("block", self.px)
        h, w = len(rows), max(len(r) for r in rows)
        out = []
        for x, y in e["points"]:
            # punto = centro de la base; con la luz del fondo alrededor
            left, top = x - w * s // 2, y - h * s
            light = self._light((left - 15, top - 15, left + w * s + 15, top + h * s + 15))
            out.append((left, top, light))
        return {"places": out, "rows": rows, "pal": pal, "s": s}

    def sprite_tops(self, name):
        """Puntos de arriba de cada copia de un sprite (de donde sale el vapor)."""
        c = self.cache.get(name)
        if not c:
            return []
        w = max(len(r) for r in c["rows"])
        return [(left + w * c["s"] // 2, top) for left, top, _ in c["places"]]

    def _draw_sprite(self, ov, name, e, t, since):
        c = self.cache[name]
        s = c["s"]
        for left, top, light in c["places"]:
            for j, row in enumerate(c["rows"]):
                for i, ch in enumerate(row):
                    if ch in c["pal"]:
                        col = np.clip(np.asarray(c["pal"][ch], float) * light, 0, 255)
                        self._block(ov, left + i * s, top + j * s, col, 1.0, s)

    # ---- steam: vapor --------------------------------------------------------------------
    def _draw_steam(self, ov, name, e, t, since):
        sources = [tuple(p) for p in e.get("sources", [])]
        if e.get("from"):
            sources += self.sprite_tops(e["from"])
        n = e.get("particles", 5)
        height, rate = e.get("height", 24), e.get("rate", 0.5)
        colors = e.get("colors", [[240, 240, 240], [210, 214, 220]])
        alphas = e.get("alpha", [0.6, 0.4, 0.2])
        bs = e.get("block", self.px)
        for si, (x0, y0) in enumerate(sources):
            for k in range(n):
                f = (t * rate * (0.8 + 0.4 * rnd(name, si)) + k / n + rnd(name, si, k)) % 1
                y = y0 - 2 - f * height
                x = x0 + e.get("sway", 3) * math.sin(2 * math.pi * (f * 1.2 + rnd(name, si, k, "p")))
                band = min(len(alphas) - 1, int(f * len(alphas)))
                col = colors[0] if band == 0 else colors[-1]
                self._block(ov, x, y, col, alphas[band], bs)
                if f < 0.5:      # abajo el vapor es más grueso
                    self._block(ov, x + bs, y, col, alphas[band] * 0.7, bs)

    # ---- screen: pantallas de las compus --------------------------------------------------
    def _draw_screen(self, ov, name, e, t, since):
        colors = e.get("colors", [[90, 230, 140], [150, 210, 255], [230, 240, 255]])
        bright = e.get("flicker_alpha", [0.92, 1.0, 0.96])
        lvl = bright[steps(t, name, 0.08, 0.3) % len(bright)]
        if e.get("rect"):
            # De frente: fondo oscuro y renglones de código que suben
            x0, y0, x1, y1 = e["rect"]
            self._box_fill(ov, e["rect"], e.get("bg_color", [18, 28, 52]), 1.0)
            line_h = e.get("line_h", 3)
            scroll = int(t * e.get("lines_per_s", 4))
            rows = (y1 - y0) // line_h
            for r in range(rows):
                k = scroll + r
                length = int((x1 - x0 - 3) * (0.25 + 0.7 * rnd(name, k, "len")))
                indent = 2 * int(rnd(name, k, "ind") * 3)
                if rnd(name, k, "blank") < 0.15:
                    continue
                col = colors[int(rnd(name, k, "c") * len(colors))]
                yy = y0 + 1 + r * line_h
                xs = x0 + 1 + indent
                ov[yy, xs:min(x1 - 1, xs + length), :3] = np.asarray(col) * lvl
                ov[yy, xs:min(x1 - 1, xs + length), 3] = 1
            # Cursor que parpadea en el último renglón
            if int(t * 2) % 2 == 0:
                yy = y0 + 1 + (rows - 1) * line_h
                ov[yy:yy + 2, x0 + 2:x0 + 4, :3] = colors[-1]
                ov[yy:yy + 2, x0 + 2:x0 + 4, 3] = 1
        if e.get("rim"):
            # De espaldas: borde de luz alrededor del monitor
            self._box_fill(ov, e["rim"], e.get("light", [170, 210, 255]), 0.8 * lvl)

    # ---- tumbleweed: planta rodadora ------------------------------------------------------
    def _draw_tumbleweed(self, ov, name, e, t, since):
        """Bola de ramitas que cruza el piso rodando y rebotando, cada tanto (every s, con chance)."""
        every, speed = e.get("every", 90), e.get("speed", 60)
        cyc = int(t // every)
        if rnd(name, "go", cyc) >= e.get("chance", 0.5):
            return
        x0, y0, x1, y1 = e["band"]   # franja de piso que cruza: x de punta a punta, y donde apoya
        r = e.get("radius", 10)
        local = t - cyc * every
        dist = local * speed
        if dist > x1 - x0 + 4 * r:
            return
        right = rnd(name, "dir", cyc) < e.get("right_chance", 0.5)
        x = x0 - 2 * r + dist if right else x1 + 2 * r - dist
        base = y0 + rnd(name, "y", cyc) * (y1 - y0)
        hop = e.get("hop", 0.7)
        y = base - r - e.get("bounce", 6) * abs(math.sin(math.pi * local / hop))
        ang = (dist / r) * (1 if right else -1)
        colors = e.get("colors", [[214, 170, 100], [170, 128, 70], [120, 84, 44]])
        s = e.get("block", self.px)
        self._block(ov, x - r * 0.6, base, e.get("shadow", [60, 40, 30]), 0.25, None)   # sombra en el piso
        self._block(ov, x + r * 0.2, base, e.get("shadow", [60, 40, 30]), 0.25, None)
        spokes = e.get("spokes", 14)
        for k in range(spokes):
            for j, f in enumerate(e.get("rings", [0.25, 0.45, 0.65, 0.85, 1.0])):
                a = ang + 2 * math.pi * k / spokes + j * 0.7
                self._block(ov, x + math.cos(a) * r * f, y + math.sin(a) * r * f, colors[(k + j) % len(colors)],
                            1.0, s)

    def _prep_spill(self, name, e):
        shape, box = self._iso_glow(e["center"], e["radius"], e.get("bands", 2))
        return {"shape": shape, "box": box}

    def _draw_spill(self, ov, name, e, t, since):
        """Reflejo de una pantalla sobre quien la mira (stage over)."""
        lvl = e.get("flicker_alpha", [0.8, 1.0, 0.9])[steps(t, name, 0.08, 0.3) % 3]
        c = self.cache[name]
        self._blend(ov, c["shape"] > 0, e.get("light", [170, 210, 255]), c["shape"] * e.get("alpha", 0.3) * lvl, c["box"])
