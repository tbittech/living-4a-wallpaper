"""Tema activo: dónde están los fondos, los personajes y la escena de cada escenario.

Cada tema vive en themes/NOMBRE/ con esta forma:
    theme.json      fondos, escena (zona caminable y lugares), roles, animaciones y reparto
    backgrounds/    imágenes originales de los fondos
    aligned/        fondos alineados (los genera align_backgrounds.py)
    characters/P/   source/ (hoja de referencia) + sprites, anims/ y atlas de cada personaje

El tema se elige con --theme NOMBRE o, si no se pasa, con config.json en la raíz.
Un tema puede vivir en otra carpeta: config.json -> "theme_paths": {"big_bang": "../Assets BBTheory"}.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
CONFIG = ROOT / "config.json"


class Theme:
    def __init__(self, name):
        self.name = name
        self.dir = theme_paths().get(name, THEMES / name)
        path = self.dir / "theme.json"
        if not path.exists():
            have = [p.name for p in THEMES.iterdir() if (p / "theme.json").exists()]
            have = ", ".join(have + list(theme_paths()))
            raise SystemExit(f"No existe el tema '{name}' ({path}). Temas: {have}")
        self.data = json.loads(path.read_text(encoding="utf-8"))
        self.backgrounds = self.dir / "backgrounds"
        self.aligned = self.dir / "aligned"
        self.characters = self.dir / "characters"

    @property
    def scene(self):
        return self.data.get("scene", {})

    @property
    def sprite_scale(self):
        return self.scene.get("sprite_scale", 4)

    def character(self, name):
        return self.characters / name

    def place_key(self, key, who=None, taken=()):
        """Lugar concreto de un lugar, rol o grupo de asientos (couch, desk...).

        En un grupo de asientos va al del personaje (scene.owners); si no tiene o está ocupado, al que
        prefiere aunque sea de otro (scene.prefers), si no al primero libre que no sea de otro, y si no
        queda ninguno, al primero libre.
        """
        places = self.scene.get("places") or {}
        role = self.data.get("roles", {}).get(key)
        if key not in places and isinstance(role, dict):
            key = role.get("place")
        seats = self.scene.get("seats", {}).get(key)
        if not isinstance(seats, list):
            return key
        only = self.scene.get("only", {}).get(who, {}).get(key)
        if only:
            # asientos permitidos para ese personaje, en orden: el primero libre
            return ([s for s in only if s not in taken] or only)[0]
        owners = self.scene.get("owners", {})
        free = [s for s in seats if s not in taken] or seats
        mine = [s for s in free if owners.get(s) == who]
        prefers = self.scene.get("prefers", {}).get(who, [])
        liked = [s for s in free if s in prefers]
        unowned = [s for s in free if s not in owners]
        return (mine or liked or unowned or free)[0]

    def place(self, key, who=None, taken=()):
        """Coordenadas de un lugar del tema, un rol genérico (shell, read, rest...) o un grupo de asientos."""
        places = self.scene.get("places") or {}
        key = self.place_key(key, who, taken)
        if places.get(key) is None:
            raise SystemExit(f"El tema '{self.name}' no tiene el lugar '{key}' marcado todavía")
        p = places[key]
        if isinstance(p, dict):
            x, y = self.grid.center(*p["tile"])
            dx, dy = p.get("offset", (0, 0))   # asiento que no cae en el centro de la casilla
            return x + dx, y + dy
        return tuple(p)

    def facing(self, key, who=None, taken=()):
        """Dirección a la que se mira en un lugar (solo temas con grilla), o None."""
        p = (self.scene.get("places") or {}).get(self.place_key(key, who, taken))
        return p.get("facing") if isinstance(p, dict) else None

    @property
    def grid(self):
        """Grilla isométrica de casillas, o None si el tema usa un polígono caminable."""
        if "grid" not in self.scene:
            return None
        from grid import IsoGrid
        return IsoGrid(self.scene)

    def animation(self, name):
        """(cuadros, fps, loop) por defecto; 4 / 6 / loop si el tema no la define."""
        a = self.data.get("animations", {}).get(name, {})
        return a.get("frames", 4), a.get("fps", 6), a.get("loop", True)


def theme_paths():
    """Temas que viven fuera de themes/ (por ejemplo, en otra carpeta de assets)."""
    if not CONFIG.exists():
        return {}
    paths = json.loads(CONFIG.read_text(encoding="utf-8")).get("theme_paths", {})
    return {k: (ROOT / v).resolve() for k, v in paths.items()}


def active_name():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    return "breaking_bad"


def load(name=None):
    return Theme(name or active_name())


def add_arg(ap):
    ap.add_argument("--theme", help=f"tema dentro de themes/ (por defecto el de config.json: {active_name()})")
