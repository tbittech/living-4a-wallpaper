"""Grilla isométrica de casillas (lógica tipo Habbo) de un tema.

theme.json -> scene.grid:
    origin  esquina de la casilla (0, 0) en píxeles del fondo alineado
    u, v    paso en píxeles al avanzar una casilla en a (abajo-izquierda) y en b (abajo-derecha)
scene.tiles: casillas caminables, por fila {"a": [[b0, b1], ...]} (b1 incluido)
scene.places: {"lugar": {"tile": [a, b], "facing": "down_right", "offset": [dx, dy] opcional}}
scene.facings (opcional): reemplaza FACINGS, {"dirección": {"step": [da, db], "view": "...", "flip": bool}}.
    Sirve para escenarios de costado (la van), donde a es la profundidad y b va de izquierda a derecha.

Se camina de casilla en casilla por los dos ejes del piso (4 direcciones de pantalla).
"""
from collections import deque

import numpy as np

# Dirección -> (paso en a, paso en b), vista del sprite y si se espeja
FACINGS = {
    "down_right": ((0, 1), "three_quarter", False),
    "down_left": ((1, 0), "three_quarter", True),
    "up_right": ((-1, 0), "back", False),
    "up_left": ((0, -1), "back", True),
}


class IsoGrid:
    def __init__(self, scene):
        g = scene["grid"]
        self.origin = np.array(g["origin"], float)
        self.u = np.array(g["u"], float)
        self.v = np.array(g["v"], float)
        self.inv = np.linalg.inv(np.column_stack([self.u, self.v]))
        self.facings = facings_of(scene)
        self.walkable = {(int(a), b) for a, runs in (scene.get("tiles") or {}).items()
                         for b0, b1 in runs for b in range(b0, b1 + 1)}

    def corner(self, a, b):
        return self.origin + a * self.u + b * self.v

    def center(self, a, b):
        """Punto donde van los pies en la casilla (a, b)."""
        x, y = self.corner(a + 0.5, b + 0.5)
        return int(round(x)), int(round(y))

    def polygon(self, a, b):
        return [tuple(self.corner(a + da, b + db)) for da, db in ((0, 0), (1, 0), (1, 1), (0, 1))]

    def tile_at(self, x, y):
        a, b = self.inv @ (np.array([x, y], float) - self.origin)
        return int(np.floor(a)), int(np.floor(b))

    def path(self, start, goal, blocked=()):
        """Camino más corto de casilla en casilla (sin contar start). None si no hay.

        start y goal pueden no ser caminables (un asiento del sillón, la silla del escritorio).
        """
        free = self.walkable - set(blocked)
        prev = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                out = []
                while cur != start:
                    out.append(cur)
                    cur = prev[cur]
                return out[::-1]
            for (da, db), _, _ in self.facings.values():
                nxt = (cur[0] + da, cur[1] + db)
                if nxt not in prev and (nxt in free or nxt == goal):
                    prev[nxt] = cur
                    q.append(nxt)
        return None


def facings_of(scene):
    """Direcciones del tema: scene.facings o, si no tiene, las isométricas de FACINGS."""
    f = scene.get("facings")
    if not f:
        return FACINGS
    return {k: (tuple(v["step"]), v["view"], bool(v["flip"])) for k, v in f.items() if not k.startswith("_")}


def facing_of(step, facings=FACINGS):
    """Dirección de pantalla de un paso (da, db) entre casillas vecinas."""
    for name, (d, _, _) in facings.items():
        if d == tuple(step):
            return name
    raise ValueError(f"paso no válido: {step}")


def tiles_to_rows(tiles):
    """{(a, b)} -> {"a": [[b0, b1], ...]} para guardar en theme.json."""
    rows = {}
    for a in sorted({t[0] for t in tiles}):
        bs = sorted(b for aa, b in tiles if aa == a)
        runs = [[bs[0], bs[0]]]
        for b in bs[1:]:
            if b == runs[-1][1] + 1:
                runs[-1][1] = b
            else:
                runs.append([b, b])
        rows[str(a)] = runs
    return rows
