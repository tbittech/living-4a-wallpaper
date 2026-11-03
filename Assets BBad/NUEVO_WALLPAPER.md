# Cómo hacer otro wallpaper en vivo (como el living de Big Bang)

Guía para armar un tema nuevo: un escenario pixel art isométrico donde cada IA (Claude, Codex, Gemini) es un personaje que entra, camina, trabaja y se va según lo que hace la IA real. Todo lo de abajo ya existe y se probó con el tema `big_bang` (`Assets BBTheory/`). El otro tema, `breaking_bad` (`Assets BBad/themes/breaking_bad/`), está en pausa pero sirve de ejemplo de escenario sin grilla.

Documentos relacionados: `IDEA_Y_ANIMACION.md` (idea y máquina de estados), `CONEXION.md` (formato de eventos), `../WALLPAPER.md` (plan del wallpaper), `../Assets BBTheory/BIG_BANG.md` (todo lo que se hizo en Big Bang, con decisiones y comandos exactos), `../wallpaper/INSTALAR.md` (instalar en otra PC).

---

## 1. Cómo está armado

```
Assets BBad/
  config.json            tema activo de las herramientas + "theme_paths" (temas en otra carpeta)
  tools/                 herramientas genéricas (sirven para cualquier tema)
  themes/<tema>/         un tema puede vivir acá...
Assets BBTheory/         ...o en su propia carpeta (registrada en theme_paths)
  theme.json             TODO lo del tema: fondos, grilla, lugares, roles, animaciones, reparto
  backgrounds/           fondos originales (día, noche sin agentes, noche con agentes)
  aligned/               fondos alineados + aligned/layers/<fondo>/<mueble>.png
  characters/<P>/        source/ (hojas de Gemini), vistas, anims/, atlas.png/.json, PROMPTS.md
  props/                 objetos agregados al fondo (pizarrón...)
  *.py                   scripts propios del tema (marcar grilla, recortar muebles, retoques de animación)
wallpaper/
  export_bundle.py       theme.json + imágenes -> wallpaper/public/bundle/<tema>/
  public/                la página (JS plano, sin build) + config.json del wallpaper
  server/                servidor aiohttp: estáticos, WebSocket, procesos, call_logs de OmniRoute
  hooks/                 hook de Claude Code
  scripts/               instalar, Lively, arranque con Windows
```

Flujo de datos: **IA real → (hook de Claude / procesos / call_logs de OmniRoute) → server.py → WebSocket → página → personaje**. La página no sabe nada del tema salvo lo que trae el bundle y `config.json`.

---

## 2. Pasos para un tema nuevo

Todos los comandos se corren desde `E:\ProyectosIA` con `python -I`. Las herramientas toman `--theme <nombre>`; si no, usan `Assets BBad/config.json` → `theme`.

### 2.1 Carpeta y registro
1. Crear `Assets <Tema>/` con `backgrounds/`, `characters/` y un `theme.json` (copiar el de Big Bang y vaciar `scene.tiles`, `places`, `layers`, `effects`, `animations` que no apliquen).
2. Registrarlo en `Assets BBad/config.json` → `theme_paths: {"<tema>": "../Assets <Tema>"}`.

### 2.2 Fondos
1. Generar 3 fondos isométricos del mismo encuadre: `day`, `night_idle` (sin IAs) y `night_active` (con IAs trabajando: pantallas prendidas, luces). Con la skill `imagen` (§4) o a mano en Gemini.
2. `theme.json` → `backgrounds`: `reference` (el que manda), `sources` (archivo de cada estado) y `align_box` (zona que tiene que quedar fija).
3. `python -I "Assets BBad/tools/align_backgrounds.py" --theme <tema>` → `aligned/<estado>.png` + `alignment.json`. Big Bang quedó en **1372×764**. Si los fondos vienen más grandes, `backgrounds.output_scale` los achica (la van: 0.5 → 1342×760).

### 2.3 Grilla, lugares y asientos
1. Marcar la grilla isométrica (lógica tipo Habbo: una persona por casilla, 4 direcciones diagonales). En Big Bang se hizo con un script propio, `Assets BBTheory/mark_grid.py` (ajusta las líneas entre baldosas del fondo de día; el piso, los muebles que bloquean y los lugares se dibujan a mano en píxeles). Copiarlo y cambiar los polígonos.
2. Lo que queda en `theme.json` → `scene`:
   - `grid` (`origin`, `u`, `v`: paso en píxeles por casilla en cada eje; ~42×21 en Big Bang), `tiles` (casillas caminables por fila).
   - `facings` (opcional): direcciones propias para escenarios de costado. La van usa una grilla rectangular (a = profundidad, b = izquierda a derecha) donde moverse a los costados es la vista 3/4 y alejarse la de espaldas (`breaking_bad/mark_grid.py`).
   - `places`: `{"lugar": {"tile": [a, b], "facing": "down_right", "offset": [dx, dy]}}`. Hacen falta al menos `door` y un lugar de salida (`exit`), uno por rol (§3) y uno de reposo.
   - `seats` (grupos de asientos: `couch`, `desk`), `owners` (asiento de cada personaje), `prefers`, `only`, `footprints` (huella de cada mueble en casillas).
3. Revisar con `compose_scene.py --debug` (casillas y lugares dibujados) y `walk_preview.py` (GIF caminando entre dos lugares).

### 2.4 Muebles en primer plano
Para caminar *detrás* de un mueble hay que recortarlo como capa. `Assets BBTheory/cut_layers.py` (propio del tema: un polígono aproximado por mueble + GrabCut, recorta los 3 fondos con la misma máscara) → `aligned/layers/<fondo>/<mueble>.png` y `scene.layers`. `tools/layers.py` decide quién tapa a quién por la huella. Objetos agregados que no están en el fondo van en `scene.props`.

### 2.5 Personajes
1. **Hoja de referencia** (4 vistas: frente, 3/4, espalda, perfil, sobre magenta #FF00FF). `python -I "Assets BBad/tools/extract_sheet.py" HOJA.jpg <Nombre> --theme <tema> [--order ...] [--height 110]` → vistas nativas + `meta.json`. Ojo con el orden de las vistas (Penny venía distinto). En Big Bang los personajes miden ~38×112 nativo con `sprite_scale` 1 (de la altura de la puerta).
2. **Prompts**: un `characters/<Nombre>/PROMPTS.md` con un bloque base (descripción fija del personaje, magenta, sin texto, pies alineados, "igualá la pose de la segunda hoja") y un bloque por animación. Copiar el de Penny como plantilla. Para animaciones comunes a todos, un prompt universal (ver `Assets BBTheory/PROMPT_SALUDO.md`).
3. **Hojas de animación**: generarlas con la skill `imagen` pasando la hoja del personaje + la misma animación de otro personaje como referencia de pose. Guardar en `source/<anim>.<ext>`.
4. **Extraer**: `python -I "Assets BBad/tools/extract_anim.py" source/<anim>.jpg <nombre> <anim> --theme <tema>` → `anims/<anim>.png/.json` y rearma el atlas. Opciones útiles: `--pick 2,3,4,3` (elegir y ordenar cuadros, descarta los de otra vista), `--fps`, `--loop/--no-loop`, `--keep-y` (saltos), `--height 0.8` (sentados), `--lower N` / `--shift N` (encajar en sillas), `--rebuild` (solo atlas).
5. Mínimo por personaje: `idle`, `walk`, `walk_back` y las de sus roles (`type`, `write`, `think`, `read`, `sit`, `look`); `wave` para entrar y salir.

### 2.6 Roles, animaciones y reparto (`theme.json`)
- `roles`: rol genérico → lugar y animación del tema (§3).
- `animations`: por animación `frames`, `fps`, `loop`, `height`, `lower`, `shift` y sus variantes `*_by_character`.
- `cast`: qué personaje es cada IA (`claude`, `codex`, `gemini`).

### 2.7 Efectos por código (opcional)
`theme.json` → `scene.effects`, implementados en `tools/effects.py` (Python, para previews) y portados a `wallpaper/public/js/effects.js` con el mismo azar: `glow` (tele que parpadea), `board` (pizarrón que se escribe solo), `clouds`, `lights` (ciudad por la ventana), `sprite`. Sumar un tipo nuevo = implementarlo en los dos lados.

### 2.8 Exportar y ver
1. `wallpaper/public/config.json` → `"theme": "<tema>"`.
2. `python -I wallpaper/export_bundle.py --theme <tema>` → `wallpaper/public/bundle/<tema>/` (bundle.json, fondos con props, capas, atlas, efectos precalculados y escenas de referencia).
3. Probar en el navegador con el servidor corriendo: `http://127.0.0.1:8765/?demo=1&debug=1&sources=claude,codex,gemini`. `?ref=<escena>&diff=1` compara contra la escena hecha en Python.
4. Lively: `powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\lively_mode.ps1 live` (o `demo`).

---

## 3. Roles genéricos

Lo que hace la IA se traduce a un rol; cada tema decide dónde y cómo se ve.

| Rol | Cuándo | Big Bang |
|---|---|---|
| `entry` | entra / se va | `door` / `exit` |
| `shell` | Bash, PowerShell, exec_command | escritorio, `type` |
| `edit` | Edit, Write, apply_patch | pizarrón, `write` |
| `read` | Read, Grep, Glob | sillón, `read` |
| `web` | WebSearch, WebFetch | ventana/telescopio, `look` |
| `think` | pensando entre herramientas | pizarrón, `think` |
| `rest` | sin hacer nada | sillón, `sit` |
| `scene` | escenas especiales | centro |

Qué herramienta va a qué rol: `wallpaper/public/config.json` → `tool_roles`.

---

## 4. Herramientas

### Genéricas (`Assets BBad/tools/`)
| Archivo | Qué hace | Funciones / clases |
|---|---|---|
| `theme.py` | carga el tema activo o `--theme`; resuelve rutas | `Theme`, `load`, `active_name`, `theme_paths`, `add_arg` |
| `align_backgrounds.py` | alinea los fondos a la referencia y los recorta al mismo tamaño | `coarse_fit`, `refine`, `edge_score` |
| `extract_sheet.py` | hoja de referencia de 4 vistas → sprites nativos | `fit_grid`, `sample_grid`, `quantize`, `defringe`, `split_views` |
| `extract_anim.py` | hoja de animación → cuadros nativos alineados por los pies + atlas | `extract`, `detect_grid`, `snap_palette`, `split_frames`, `place_frames`, `build_atlas` |
| `grid.py` | grilla isométrica, camino más corto, dirección | `IsoGrid`, `facing_of`, `tiles_to_rows` |
| `layers.py` | muebles en primer plano y quién tapa a quién | `load`, `background`, `covers`, `compose` |
| `effects.py` | efectos por código (glow, board, clouds, lights, sprite) | `Effects` |
| `compose_scene.py` | foto de prueba: fondo + personajes en lugares | `NOMBRE@LUGAR[:VISTA][:left]`, `--debug`, `--effects` |
| `walk_preview.py` | GIF/MP4 caminando por la grilla | `walk_steps`, `hold`, `with_trail`, `save_gif` |

### Propias de Big Bang (`Assets BBTheory/`, copiar y adaptar)
| Archivo | Qué hace |
|---|---|
| `mark_grid.py` | marca grilla, piso, muebles que bloquean y lugares |
| `cut_layers.py` | recorta muebles como capas (GrabCut) |
| `walk_cycle.py` | caminata con paso a partir de un solo cuadro de zancada (espeja piernas, traslada zapatos) |
| `walk_arms.py` | balanceo de brazos en la caminata |
| `walk_from_leonard.py` | caminata usando las piernas de otro personaje |
| `idle_breathe.py` | idle que respira y parpadea a partir de un cuadro quieto |
| `blanket_sheet.py` | hoja de 3 filas → 3 animaciones con ancla propia |

Cuando Gemini no logra una animación (piernas que no alternan, cuadro único), estos scripts la arman por código.

### Wallpaper
| Archivo | Qué hace |
|---|---|
| `export_bundle.py` | tema → bundle del frontend |
| `public/js/main.js` | arranque, bucle a 30 FPS, dibujo; parámetros `?demo`, `?debug`, `?bg`, `?fit`, `?leave`, `?sources`, `?ref` |
| `public/js/bundle.js`, `grid.js`, `layers.js`, `effects.js`, `scaler.js` | carga del bundle y ports de las herramientas Python; escalado sharp-bilinear |
| `public/js/net.js` | WebSocket al servidor con reconexión |
| `public/js/demo.js` | simulador de eventos (`?demo=1`; `?demo=manual` solo teclas) |
| `public/js/sim/character.js` | máquina de estados del personaje (ABSENT, ENTERING, IDLE, THINKING, WORKING, LEAVING, SCRIPTED) |
| `public/js/sim/world.js` | lugares, asientos con dueño, ocupación |
| `public/js/sim/scenes.js` | guiones (`walk`, `play`, `fade`, `wait`, `face`, `swap`, `trail`): paseo, disputas, Flash, Wii, manta, Hobbit |
| `public/js/sim/chatter.js` | frases: cruces, sofá, saludos, despedidas |
| `server/server.py` | estáticos + `/ws` + `/event` + `/state`; guarda el estado |
| `server/procs.py` | quién está: procesos de Windows y WSL (claude.exe, codex.exe, gemini en node) |
| `server/calls.py` | qué hacen Codex y Gemini: lee los `call_logs` de OmniRoute |
| `server/state.py` | estado por IA y validación de eventos (nunca viaja texto libre) |
| `hooks/cc_hook.py` | hook de Claude Code; arranca el servidor si no está |
| `scripts/` | `install.ps1`/`uninstall.ps1`, `hooks_setup.py`, `lively_mode.ps1`, `install_startup.ps1` |
| `tools/send_event.py`, `tools/sim_test.mjs` | mandar eventos a mano; simulación larga en Node (choques, trabados) |

### Skills de Claude
- **`imagen`**: genera imágenes con Gemini Flash Image vía OmniRoute, con referencias. `generar_imagen.ps1 -Prompt ... -Ref a.jpg,b.webp -Out ruta_sin_ext`. Cuota semanal compartida con los Gemini Flash (~500-1000 requests por cuenta). Después de actualizar OmniRoute hay que volver a correr `patch_omniroute.py`.
- **`delegar`**: manda trabajo mecánico o segundas opiniones a Gemini/Codex por OmniRoute.

---

## 5. Lo que es propio de Big Bang (cambiar en un tema nuevo)

El motor es genérico, pero estas partes nombran a Sheldon, Leonard y Penny:
- `public/js/sim/chatter.js`: todas las frases (por personaje y por pareja).
- `public/js/sim/scenes.js`: escenas especiales (Flash, Wii, manta, Hobbit) y sus disparadores en `config.json` → `scenes`.
- `config.json`: `home`, `disputes`, `place_disputes`, `costumes`, `chatter`, `scenes`.
- Personajes extra para disfraces (`sheldon_flash`, `leonard_hobbit`).

Para un tema nuevo conviene arrancar con escenas y frases vacías, y sumarlas cuando el resto ande. Lo propio de cada tema va en `config.json` → `themes.<tema>` (pisa las claves generales; ver `breaking_bad`). Las escenas de referencia de `export_bundle.py` (`?ref=`) van en `theme.json` → `refs`.

---

## 6. Lecciones aprendidas

- Pedir a Gemini **siempre magenta plano**, sin texto ni sombras, pies a la misma altura, y pasar dos referencias (el personaje + la misma animación de otro personaje). Aun así mezcla vistas: se arregla con `--pick`.
- Las hojas suelen venir a media resolución o con "píxeles falsos" grandes; `extract_*` detecta la grilla sola, pero si la calidad da baja hay que forzar la celda.
- Caminatas: Gemini casi nunca alterna bien las piernas. Mejor un cuadro bueno + `walk_cycle.py`.
- Sentados: misma altura de cabeza que parados; encajar con `lower`/`shift` por personaje.
- Escala: personajes de la altura de la puerta se leen bien en un fondo de ~1372 de ancho.
- Probar todo con `?demo=1&debug=1` y con `sim_test.mjs` (`node wallpaper/tools/sim_test.mjs <semilla> <tema>`: 30 min simulados, 0 choques) antes de ponerlo en Lively.
- La skill `imagen` atiende **de a una** imagen: varias en paralelo se cortan por tiempo. Si la cuota se agota (429), `code_anims.py` de la van arma `idle`/`walk`/`walk_back` provisorios desde las vistas.
- `sprite_scale` > 1: el exportador agranda los atlas (el frontend dibuja a tamaño nativo).
