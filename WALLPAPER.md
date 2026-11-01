# Wallpaper: el living 4A en vivo

Plan para pasar de las herramientas offline (PNG/GIF/MP4) al fondo de pantalla en vivo: frontend en el navegador + servidor de eventos.
La idea es **reusar todo lo que ya generó el pipeline de Python** y portar a JS solo lo que corre en cada cuadro.
Lo visual general está en [IDEA_Y_ANIMACION.md](IDEA_Y_ANIMACION.md), la conexión en [CONEXION.md](CONEXION.md) y el tema en [BIG_BANG.md](Assets%20BBTheory/BIG_BANG.md).

> **Estado:** fases 1, 2 y 3 hechas (§7), más la disputa por el sillón y Flash adelantadas de las fases 5 y 6. Sigue la fase 4 (Lively + arranque).

**Cómo correrlo** (desde `E:\ProyectosIA`):

```
python -I wallpaper/export_bundle.py
python -m http.server 8765 --bind 127.0.0.1 --directory wallpaper/public
```

Abrir `http://127.0.0.1:8765/?demo=1&debug=1` (o `?demo=manual` para manejarlo solo con teclas). En Claude Code también está como `wallpaper-demo` en `.claude/launch.json`.

**Con Claude real** (fase 3): `python wallpaper/server/server.py` (o `--port 8775`; también `WALLPAPER_PORT`) sirve lo mismo más `/ws`, `/event` y `/state`. Abrir `http://127.0.0.1:8765/` (`?debug=1` muestra el estado de la conexión y deja las teclas del simulador). Los hooks (eventos en `wallpaper/hooks/settings_snippet.json`) los pone `wallpaper/install.bat` en `%USERPROFILE%\.claude\settings.json` con la ruta real de la carpeta (ver [wallpaper/INSTALAR.md](wallpaper/INSTALAR.md)). `?server=127.0.0.1:8775` conecta a otro puerto (por ejemplo con la página servida por `http.server`). `python wallpaper/tools/send_event.py tool_call --tool Bash` manda eventos a mano.
Hay que volver a exportar el bundle cada vez que cambian `theme.json`, los fondos, las capas o los atlas.
Prueba sin pantalla de la simulación: `node wallpaper/tools/sim_test.mjs [semilla]` corre la demo 30 minutos simulados y cuenta estados, lugares, choques y globos (da 0 choques con los tres personajes).
Con `?debug=1`, la consola tiene `__sim.advance(segundos)` (adelanta la simulación a pasos fijos y dibuja; pausa el bucle real hasta `__sim.resume()`) y `__sim.onEvent({...})` para mandar eventos.
`?ref=couch_night` (o `shell_night`, `edit_day`, `idle_night`) dibuja una escena de referencia de Python y muestra cuántos píxeles difieren; `&diff=1` pinta las diferencias.

**Guiones** (`public/js/sim/scenes.js`, configurados en `config.json` → `scenes`, `disputes`, `costumes`): escenas que toman el control de un personaje y después lo devuelven a su rol.
- **Disputa por el sillón:** `couch_right` es de Sheldon y Penny lo prefiere (`scene.prefers`). Si Sheldon va a su lugar y hay alguien sentado, se para enfrente: «Penny... ese es mi lugar.», ella contesta «¡Ok, ok!» y se pasa a otro asiento. Si el otro todavía iba caminando, Sheldon lo reclama y el otro busca otro asiento sin discutir. Solo discuten los de `disputes`.
- **Paseo:** sentado en reposo más de 45 s, a veces da una o dos vueltas (cocina, ventana, centro o una casilla libre) y vuelve.
- **Sheldon Flash:** sentado en reposo más de 5 min, 25 % cada 10 s, enfriamiento de 45 min: la puerta, el traje, la pose, el recorrido a 12 casillas/s con estela, la pose y la vuelta. Un evento lo corta: corre a la puerta, se saca el traje y va a trabajar.
- **Leonard Frodo:** mismas condiciones que Flash (`scenes.hobbit`; nunca las dos a la vez): el pasillo, el disfraz, camina a una casilla lejana y a la vista, se pone el Anillo (destello), se disuelve con tramado y chispas mientras la escena se va al gris, reaparece lejos y se lo saca (1 o 2 veces), y vuelve al pasillo como Leonard. Un evento lo corta: vuelve a verse, va al pasillo y se cambia.
- **Asientos de Penny** (`scene.only` en `theme.json`): en el sillón solo el lugar de Sheldon (y la discusión sigue), en los escritorios solo la compu de Leonard; si están ocupados, la banqueta de la cocina (`kitchen_stool`). En la banqueta, `type` (el celular) se sube a la altura del asiento (`Character.lift`).
- **Wii** (`scenes.wii`, solo Sheldon): en reposo más de 60 s, 20 % cada 10 s y enfriamiento de 10 min, se para detrás de la tele (`tv`: la tele le tapa las piernas) y juega al bowling de 2 a 4 tiradas (`wii`). Un evento lo corta.
- **Manta y notebook** (`scenes.blanket`, solo Sheldon, ya sentado en el sillón): `blanket_on` → `blanket_type` en loop → `blanket_off` (BIG_BANG.md §6). Prueba en reposo con las mismas condiciones que la Wii, tecleando un rato corto (15–45 s) o largo (2–6 min) al azar (`type`). En reposo, un evento lo corta: se destapa (`blanketOff`) y va a su rol. **Uso alto:** si el turno de Claude viene con esfuerzo Alto, Extra o Máx (`effort` del hook, `scenes.blanket.high`), trabaja todo el turno en el sillón con la manta, tecleando sin límite (`startBlanket(hold)`), y se destapa al terminar el turno.
- Teclas de la demo: **F** fuerza Flash, **H** Frodo, **W** un paseo, **G** Wii, **M** manta.

---

## 1. Arquitectura

Carpeta nueva: `E:\ProyectosIA\wallpaper\`

```
wallpaper/
  export_bundle.py          theme.json + atlas + capas + props + efectos -> public/bundle/<tema>/
  server/server.py          aiohttp: estáticos + /ws + /event + /state
  server/state.py           estado grueso por source (para el snapshot)
  hooks/cc_hook.py          hook de Claude Code: stdin -> evento normalizado -> POST
  tools/send_event.py       mandar eventos a mano (pruebas)
  scripts/install_task.ps1  tarea programada al iniciar sesión
  public/
    config.json             tema, fps, horarios día/noche, tiempos, home por personaje, herramienta -> rol
    index.html
    js/main.js              arranque, bucle, parámetros de la URL
    js/bundle.js            carga bundle.json + imágenes, arma los atlas espejados
    js/scaler.js            escalado a la pantalla
    js/grid.js              port de grid.py
    js/layers.js            port de layers.compose / covers
    js/effects/*.js         glow, board, clouds, lights, sprite, steam, screen, spill
    js/sim/world.js         ocupación de casillas, reservas, asientos, día/noche
    js/sim/character.js     máquina de estados por personaje
    js/sim/director.js      interacciones y escenas especiales (guiones)
    js/sim/scenes/flash.js, frodo.js
    js/net.js               WebSocket con reconexión
    js/demo.js              simulador de eventos (?demo=1) + teclas de debug
    js/font.js              fuente bitmap 5x7 para los globos
    bundle/big_bang/        GENERADO por export_bundle.py (no se edita a mano)
```

**Stack**
- **Frontend:** Canvas 2D, JS plano con módulos ES nativos, sin build ni dependencias. Lively usa WebView2 (Chromium): hay `ctx.filter`, `OffscreenCanvas` y módulos.
- **Servidor:** **Python + aiohttp** (única dependencia). El pipeline de assets es Python: `export_bundle.py` importa `theme.py`, `layers.py` y `effects.py` tal cual, y el mismo Python corre servidor y hook. De claude-office (probablemente Node/TS) solo se toma la idea del mapeo de hooks; no hace falta fork.
- **Estático:** todo `public/`. Dinámico: `/ws`, `/event`, `/state`, `/config.json`. Escucha **solo en `127.0.0.1:8765`**.

---

## 2. Exportación de datos (`export_bundle.py`)

`python -I wallpaper/export_bundle.py --theme big_bang` (el tema se pasa explícito: `Assets BBad/config.json` sigue en `breaking_bad`).

**Salida** en `public/bundle/big_bang/`:

```
bundle.json
bg/<day|night_idle|night_active>.png     layers.background(th, bg)  (props ya pintados)
layers/<bg>/<mueble>.png                 copia de aligned/layers/<bg>/
layers/<bg>/<prop>.png                   layers._prop(th, spec, bg) (pizarrón oscurecido de noche)
chars/<id>/atlas.png                     copia; <id> en minúscula (la carpeta es "Sheldon")
fx/<efecto>.<bg>.png | .json             volcado de effects.Effects(th, bg).cache
```

**`bundle.json`**
- `size: [1372, 764]`, `sprite_scale`, `fx_px`.
- `grid: {origin, u, v}`, `walkable: [[a,b], ...]` (expandido de `scene.tiles`, como `IsoGrid.__init__`).
- `places: {key: {tile, facing, offset, foot: [x,y]}}`: `foot` precalculado con `th.place(key)` (mismo redondeo que Python).
- `facings`: tabla `FACINGS` de `grid.py`.
- `seats`, `owners`, `roles`, `cast`, `animations`.
- `layers: [{name, pos, tiles, depth, img: {day, night_idle, night_active}}]`: muebles y props, en el orden de `layers.load`.
- `characters: {sheldon: {atlas, size, anims}}` con `atlas.json["animations"]` (incluye `ref_*`; el `anchor` ya trae `lower`).
- `variants: {sheldon: {flash: "sheldon_flash"}, leonard: {hobbit: "leonard_hobbit"}}`.
- `effects`: `scene.effects` + ruta de lo precalculado por efecto y fondo.
- `live`: **sección nueva** en `theme.json` con lo propio del tema: `home` por personaje (Sheldon y Leonard → `hallway`, Penny → `door`, vive enfrente), `wander_places: ["kitchen","window","center"]`, `flash.route` (la `ROUTE` de `flash_preview.py`), parámetros de Frodo (`JUMPS`, `MIN_JUMP`, `TINT`, `DARK` de `frodo_preview.py`).

**Se precalcula en Python (no se porta):** fondos con props, props oscurecidos, y todos los `_prep_*` de `effects.py` (forma del `glow` y su máscara `behind`, máscara de cielo y nubes, puntos de `lights`, dibujito `takeout` con la luz de cada fondo, forma del `spill`, píxeles de tinta del `board` ya ordenados). Regla: arreglo 2D → PNG; vectores → JSON.

**Se porta a JS:**
- `grid.js`: `center`, `tileAt`, `path` (en `grid.py` es **BFS**; con 286 casillas alcanza) y `facingOf`. `start` y `goal` pueden no ser caminables (asientos).
- `place_key` de `theme.py` (asiento propio → sin dueño → primero libre).
- `layers.js`: `covers`, `_overlap` y `compose` completo (orden topológico con desempate por pies).
- `effects/*.js`: solo los `_draw_*`, con `fillRect` en bloques de `px`. El azar con un hash propio; no se busca paridad al píxel, solo el mismo comportamiento.
- `with_trail` / `ghost` / `fade` de `walk_preview.py` y `flash_preview.py`; `dither`, `sparks`, `glints`, `tinted` de `frodo_preview.py`. (`flash_preview.py` y `frodo_preview.py` eran los prototipos offline en `Assets BBTheory/`; ya portados, se borraron en la limpieza del 2026-11-01 y están en `D:\backupbbtheory`.)

**Paridad:** `export_bundle.py --refs` genera con `compose_scene.py` escenas de referencia en `bundle/_ref/`; el frontend con `?ref=1` dibuja las mismas para comparar a ojo.

---

## 3. Render

**Escalado: sharp-bilinear.** 1920/1372 = 1,40 y 2560/1372 = 1,87: con escala entera pura solo entra ×1.
1. Escena a resolución nativa en un canvas de 1372×764 (`imageSmoothingEnabled = false`).
2. Copia a un canvas intermedio a escala entera `k = ceil(escala_final)` (×2 en 1080p y 1440p, ×3 en 4K), sin suavizado.
3. Baja a la pantalla con `imageSmoothingQuality = "high"`: píxeles parejos, sin columnas de 1 y 2 px alternadas.

**Aspecto:** `fit=cover` por defecto (`escala = max(W/1372, H/764)`, recorte centrado; se pierden ~10 px nativos por lado en 1080p, son paredes). `fit=contain` como opción.

**Bucle:** `requestAnimationFrame` con acumulador a **30 FPS**. `dt` limitado a 100 ms; tras una pausa de más de 2 s, quien estaba caminando salta a su destino.

**Orden de dibujo por cuadro**
1. Fondo actual (en el crossfade: A y encima B con `globalAlpha = k`).
2. Efectos `under` en un canvas `fxUnder` sobre el fondo.
3. `layers.compose(actores + estela, capas)`. Cada capa que se superpone con `fxUnder` se compone en un canvas temporal con `source-atop` (equivale a `Effects.under`).
4. Efectos `over` (vapor, reflejos), tinte de escena (Frodo), chispas, globos.

**Día / noche:** `day` entre `config.day_hours = [7.5, 19.5]`; si no, `night_active` con al menos un personaje presente y `night_idle` sin nadie. Fundido de 1,5 s; se reevalúa cada 5 s y en cada cambio de presencia.

**Sprites:** atlas espejado por personaje al cargar (ancla espejada `ax' = w - 1 - ax`). Posición: `pies - anchor`.
Animación faltante: `anim → idle (si la vista es three_quarter) → ref_<vista>`, como `load_anim(...) or load_still(...)`.

**Debug** (`?debug=1`): casillas, lugares, reservas y FPS.

---

## 4. Simulación

**World** (`world.js`)
- `occupied: Map<"a,b", id>` (casilla actual de cada uno + asientos ocupados) y `reserved` (la casilla siguiente durante un paso).
- Solo se entra a una casilla reservada. Si está tomada: espera 0,6 s y recalcula con `blocked` = ocupadas y reservadas por otros; a los 3 intentos, otro asiento o casilla libre del mismo rol.
- Durante un paso tapa con la casilla `max(cur, next)` (como `walk_steps`).
- Velocidad 2,5 casillas/s; Flash a 12.

**Character** (`character.js`): `ABSENT, ENTERING, IDLE, THINKING, WORKING, LEAVING, CELEBRATE` + `SCRIPTED` (lo controla el director).

| Evento | Transición |
|---|---|
| `session_start` o primer evento estando ABSENT | ENTERING: aparece en su `home` (o `door`, con `knock` si toca) y camina al rol `rest` |
| `request_start` | THINKING: rol `think` |
| `tool_call` | WORKING(rol): `shell`→desk/`type`, `edit`→whiteboard/`write`, `read`→couch/`read`, `web`→window/`look` |
| `tool_result` | 2,5 s de gracia; si no llega otro `tool_call`, THINKING |
| `turn_end` | CELEBRATE si el turno duró más de 60 s sin `error`; si no, IDLE |
| `session_end` | LEAVING (solo cuando cierra la última sesión de ese `source`) |

- **Herramienta → rol** (`TOOL_ROLES`): tabla de IDEA §5 + nombres de Claude Code en minúscula. `bash`→shell; `edit`, `write`, `multiedit`, `notebookedit`→edit; `read`, `grep`, `glob`, `ls`→read; `websearch`, `webfetch`, `mcp__*`→web; `task`, `agent`, `todowrite`→think (con globo 📞 los subagentes); desconocida→edit.
- **Antirebote:** no cambia de lugar hasta llevar 2 s (`min_dwell`) en el actual; si el rol nuevo usa el mismo lugar, solo cambia la animación.
- **Cola:** las animaciones sin loop (`celebrate`, `knock`, `ring_on`) y SCRIPTED bloquean; los eventos se guardan y al liberarse se aplica **solo el estado final**.
- **Sin tokens:** sentado en IDLE, a los 45 s pasea (`wander_places` o casilla libre, 5–15 s en `idle`, a veces vuelve al sillón). A los 3 min sin eventos se va a su `home`: Sheldon y Leonard al **pasillo a los cuartos** (`hallway`, ya marcado), Penny a `door`. Desaparece con fundido / tramado y vuelve por el mismo lugar con el próximo evento.
- **Varias sesiones del mismo `source`:** un solo personaje; se va cuando cierran todas.

**Director** (`director.js`): las escenas son **generadores** avanzados por el tiempo de la simulación (se pausan con Lively): `yield walk(actor, tile)`, `yield play(actor, "flash_pose", 1.5)`, `yield fade(actor, out)`, `yield swap(actor, "hobbit")`, `yield bubble(actor, "Bazinga!", 2)`, `yield wait(1)`. Al terminar, el personaje vuelve al estado del último evento.
Una escena por vez, enfriamiento y probabilidad propios (`config.json → scenes`), se evalúa cada 10 s y ante eventos.

| Escena | Disparador | Prob. / enfriamiento |
|---|---|---|
| `knock` | ENTERING de Sheldon (siempre) o de otro (15 %) | 2 min |
| `couch_dispute` | Dos `source` con el mismo archivo en 60 s, o alguien en el asiento del dueño cuando este llega a `rest`: van a `center`, `argue` + globos, el que pierde va a `desk` | 50 % / 10 min |
| `bazinga` | `error` (429/5xx) de X con otro presente | 50 % / 10 min |
| `celebrate_together` | `turn_end` largo con otro en IDLE | 50 % / 5 min |
| `whiteboard_debate` | Dos activos más de 5 min seguidos | 30 % / 15 min |
| `flash` (Sheldon) | IDLE sentado más de 5 min: `flash_preview.py` paso a paso | 25 % por chequeo / 45 min |
| `frodo` (Leonard) | Igual, desde `hallway`: `frodo_preview.py` paso a paso (tramado Bayer 4×4 con 16 máscaras precalculadas y `destination-in`, chispas, tinte gris, 1–2 reapariciones en casillas visibles) | 25 % / 45 min; nunca junto con `flash` |

- Estela de Flash: cuadros "fantasma" precalculados (`blur(1.2px)` + tinte), últimos 6 con `globalAlpha = 0.55·(1 - k/7)`.
- Un evento de trabajo durante una escena especial la corta en su siguiente punto seguro: el personaje vuelve a la puerta o al pasillo y reaparece normal.

---

## 5. Servidor y conexión

**`server/server.py`** (aiohttp, `127.0.0.1:8765`)
- `GET /`, estáticos y `/config.json`.
- `GET /ws`: al conectar manda `{"type": "snapshot", "server_ts", "agents": {claude: {present, sessions, state, role, tool, since, last_ts}}}`; después cada evento como `{"type": "event", "event": {...}}`. Con varias sesiones de la misma IA, `session_end` se reenvía solo cuando cierra la última.
- `POST /event`: evento normalizado (o lista). Valida `source`, `type`, `ts`, **descarta texto libre**, actualiza `state.py` y reenvía.
- `GET /state`: estado actual (debug).

Formato: el de CONEXION §2 + `session_start` y `session_end`.

**Frontend (`net.js`):** reconexión con espera creciente (0,5 → 10 s). En la primera carga los presentes aparecen directo en su lugar; en una reconexión solo se corrige quién está.

**Modo DEMO** (`?demo=1`, anda sin servidor): sesiones verosímiles por `source` (`session_start`, ciclos `request_start` → `tool_call` → `tool_result` → … → `turn_end`, pausas de 10–300 s). Teclas: `1`–`4` shell/edit/read/web, `T` turn_end, `E` error, `F`/`H` fuerzan Flash/Frodo, `S`/`L`/`P` eligen personaje. Entran por la misma cola que los reales.

**Hook de Claude Code (`hooks/cc_hook.py`)**
- Lee el JSON de stdin (`hook_event_name`, `session_id`, `tool_name`, `tool_input`).
- `UserPromptSubmit`→`request_start`, `PreToolUse`→`tool_call`, `PostToolUse`→`tool_result`, `Stop`→`turn_end`, `SessionStart`→`session_start` (ignora `compact`; `clear` sí va, trae otro `session_id`), `SessionEnd`→`session_end`.
- Manda solo `source`, `session`, `type`, `tool` y `ts`: **nunca** `prompt`, `command`, `content`, `tool_response` ni rutas (`files` queda para OmniRoute; el servidor lo acepta).
- POST con un socket a mano (`http.client` importa `email.*` y tarda más que el resto), `python -I -S`, timeout 0,5 s, traga toda excepción, siempre `exit 0` y sin salida. El puerto lo lee de `server/.running.json`, que deja el servidor mientras corre; si no está o su proceso murió, ni se conecta (en Windows un puerto cerrado tarda todo el timeout).

Configuración (se hace en la fase 3, **fusionando** con lo que ya haya en `%USERPROFILE%\.claude\settings.json`, no pisándolo): el mismo comando para los seis hooks, ya que el evento sale de `hook_event_name`:

```json
{ "hooks": {
  "SessionStart":     [{ "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }],
  "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }],
  "PreToolUse":       [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }],
  "PostToolUse":      [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }],
  "Stop":             [{ "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }],
  "SessionEnd":       [{ "hooks": [{ "type": "command", "command": "python -I -S \"E:/ProyectosIA/wallpaper/hooks/cc_hook.py\"", "timeout": 3 }] }]
}}
```

**OmniRoute** (Codex = Leonard, Gemini = Penny): después, al mismo `POST /event` (opciones A/B/C de CONEXION §4), más `gateway_up` / `gateway_down` en el snapshot.

---

## 6. Lively Wallpaper y arranque

- Lively: *Add wallpaper → URL* → `http://127.0.0.1:8765/?fit=cover`. Configuración por query string y `config.json`.
  **Instalado (2026-10-31):** entrada `Living 4A` en `%LOCALAPPDATA%\Lively Wallpaper\Library\wallpapersbt_living4a\` (`LivelyInfo.json` con `Type: 3` = URL, `http://127.0.0.1:8765/`), puesta con `Lively.exe setwp --file <carpeta>`. El servidor corre con `pythonw.exe wallpaper\server\server.py` lanzado a mano: hasta la tarea de arranque, después de reiniciar Windows hay que volver a lanzarlo (el wallpaper reintenta solo).
- **Pausa:** "pausar con apps a pantalla completa o maximizadas"; `requestAnimationFrame` se frena solo y se escucha `visibilitychange`. Límite de FPS de Lively en 30.
- **Íconos y barra:** los íconos caen sobre la pared izquierda (la puerta está en x≈496 nativo). `?inset_bottom=48` calcula el cover sobre `H - inset` anclado arriba (los escritorios de adelante no quedan bajo la barra); `?inset_left=N` para varias columnas de íconos.
- **Arranque:** `scripts/install_task.ps1` registra la tarea "WallpaperBBT" al iniciar sesión con `pythonw.exe ...\server\server.py` (sin consola, reinicio si falla). Lively arranca solo; el frontend espera y se reconecta, el orden da igual.
- **Sin servidor:** living vacío (`night_idle` / `day`) y reintenta; nunca queda negro.

---

## 7. Fases

| # | Fase | Hecho cuando |
|---|---|---|
| 1 ✅ | **Living + Sheldon con simulador**: `export_bundle.py` (fondos, capas, props, grilla, lugares, atlas de todos los personajes), `scaler.js`, `grid.js`, `layers.js`, Character con ENTERING/IDLE/THINKING/WORKING/LEAVING, `demo.js` | Hecho: entra por `door`, rodea el sillón hasta `couch_left`, va al pizarrón (`write`), a su compu (`type`, tapado por el escritorio) y a la ventana con las teclas; sin eventos se va al pasillo y vuelve por ahí. Fundido día/noche, antirebote, espera en casillas ocupadas y salto al destino tras una pausa larga ya incluidos. ~10 ms por cuadro. **Falta mirar la nitidez en el monitor real** (el panel de prueba se ve reducido) |
| 2 ✅ | **Tres personajes y mundo completo**: reservas, `place_key` (con `prefers`), antirebote, paseo y salida a `home`, crossfade día/noche, los efectos de `scene.effects`, `?ref=` | Hecho. Efectos portados a JS con el mismo azar que Python (crc32 del `repr` de la clave): las 4 referencias de `export_bundle.py` dan 0 píxeles distintos (diferencia máx. 2/255). Lugar compartido ocupado → espera en la casilla libre de al lado; casilla bloqueada → espera, busca otro camino y a los 3 s pasa igual. Demo de 30 min con los tres: 0 choques, nadie trabado más de 0,8 s |
| 3 ✅ | **Servidor + Claude real**: `server.py`, `state.py`, `net.js`, `cc_hook.py`, hooks en settings.json | Hecho: sesión completa de hooks (inicio, prompt, Bash, Edit, Stop, fin) mueve a Sheldon en el navegador; matar y reiniciar el servidor → reconecta y el snapshot lo deja donde estaba (el estado se guarda en `server/.state.json`); hook ~85 ms (casi todo el arranque de Python; con el servidor caído ~70 ms, no se conecta); solo viajan tipo, herramienta, id de sesión y hora (ni prompt, ni comando, ni rutas). Varias sesiones: se va con la última. Hooks instalados en el settings.json real (2026-11-01) y probados con una sesión de verdad (`/state` la muestra trabajando). Para pasar Lively de demo a real: `scripts/lively_mode.ps1 live` (y `demo` para volver) |
| 4 | **Lively + arranque** | Tras reiniciar Windows aparece solo; se pausa con un juego a pantalla completa; los insets respetan la barra |
| 5 | **Interacciones**: globos (hechos: texto nítido en la pantalla con borde de bloques), ~~couch_dispute~~ (hecha), knock, bazinga, celebrate_together, whiteboard_debate | Cada una se fuerza desde la demo, respeta el enfriamiento, nunca se pisan dos |
| 6 | **Escenas especiales**: ~~Flash~~ (hecho: `scenes.js`, estela con atlas fantasma, cortable) y Frodo (pasillo y capa de la heladerita ya hechos) | Recorridos como los de los prototipos (`flash_sheldon.mp4` y `frodo_leonard.mp4`, en `D:\backupbbtheory`); un evento real corta la escena prolijamente |
| 7 | **OmniRoute**: Leonard (Codex) y Penny (Gemini) con eventos reales, `error` y `fallback` | CONEXION §8, fases 3 y 4 |

---

## 8. Riesgos y preguntas abiertas

- **Escalado:** el sharp-bilinear deja un borde levemente suave en 1080p (factor 1,41). Si no gusta, la alternativa es repintar el fondo a ×2 nativo (regenerar assets). Verlo en el monitor real.
- **Animaciones faltantes** (cadena de reemplazos mientras tanto): Sheldon `look`, `celebrate`, `argue`, `knock`; Penny `look` (en pausa, decidido); Leonard `write` / `look` provisorias; `flash_idle`.
- **Hooks en Windows:** confirmar con qué shell los corre Claude Code y si `python` está en ese PATH (si no, ruta absoluta de `python.exe`). Medir la latencia; si molesta, `curl -s -m 1 --data-binary @-` y filtrar en el servidor.
- **`files` de Claude Code** solo trae rutas de Edit/Write/Read; la disputa por archivo entre IAs distintas recién se ve con OmniRoute.
- **Efectos:** `board` pinta miles de píxeles: canvas del pizarrón que se actualiza solo cuando cambia (no cada cuadro). Medir CPU en Lively con todos los efectos.
- **Mayúsculas:** `characters/Sheldon` frente a `cast.claude = "sheldon"`; el bundle normaliza todo a minúscula.
- **claude-office sin revisar:** el plan no lo forkea; si tiene un mapeo de hooks o estado de sesión mejor, se copia sin cambiar el formato del evento.
- **Abiertas:**
  - ¿Ciclo día/noche por hora real o siempre noche?
  - ¿Cuánto es "turno largo" para festejar (60 s propuesto)?
  - ¿Pantalla principal 1920×1080 o 2560×1440? ¿Más monitores?
