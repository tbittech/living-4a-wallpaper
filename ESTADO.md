# Estado del proyecto: escena de IAs (fondo de pantalla animado)

## 2026-11-02: idle de Penny e imágenes con Gemini

**Qué se hizo**
- Idle de Penny animado por código: `Assets BBTheory/idle_breathe.py` (8 cuadros a 4 fps, respira 1 px de la cintura para arriba y parpadea cada 2 s). Original en `characters/penny/anims/idle_orig.png`, GIF en `anims/idle_preview.gif`, atlas regenerado, nota en `BIG_BANG.md`. Sin commit. No probado dentro del wallpaper.
- Gemini Flash Image (`agy/gemini-3.1-flash-image`) genera la imagen, pero OmniRoute la tiraba: el colector de Antigravity (`open-sse/executors/antigravity/sseCollect.ts`) solo junta texto y tool calls, ignora `inlineData`.
- Parche aplicado a OmniRoute 3.8.51 con `C:\Users\Casita\.claude\skills\imagen\scripts\patch_omniroute.py` (5 chunks de `dist/.build/next/server/chunks`; originales en `skills\imagen\omniroute_backup\3.8.51\`, `--restore` vuelve atrás). La imagen viaja en el texto como `![image](data:...)`. Al actualizar OmniRoute hay que volver a correrlo.
- Script nuevo `skills\imagen\scripts\generar_imagen.ps1 -Prompt ... -Ref a.jpg,b.webp -Out ruta_sin_ext` (exit 0 ok, 10 sin imagen, 3 OmniRoute caído, 2 args). Falta el `SKILL.md` de la skill `imagen`.

- Probado: `generar_imagen.ps1` con OmniRoute reiniciado devuelve la imagen (exit 0, ~1 min). Idle de Penny de Gemini en `characters/penny/source/idle_gemini.jpg`: Penny bien, cuadro 1 de frente (los otros 3 en 3/4, el 3 se acomoda el pelo) y sombras bajo los pies. Sin extraer.
- `SKILL.md` de `imagen` escrito (uso por iniciativa para hojas de sprites, fondos y props; cómo re-parchear OmniRoute).

**Hipótesis vigentes**
- Ninguna nueva.

**Descartado**
- `/v1/images/generations`: con `agy/` rechaza el nombre, con `antigravity/` da Internal error. `requestType: image_gen` y `modalities` no cambian nada. Codex image sin cuota hasta el 16/11. AI Horde no acepta referencias.

**Próximo paso**
- Mirarlo en Lively. Commit cuando el usuario diga.
- (Historia) Idle de Gemini extraído (`--pick 2,4,3,4 --fps 2`, 51×112, alturas iguales a la referencia) y guardado **fuera** de `anims/` (`source/idle_gemini.png/.json`) para no meterlo al atlas; atlas restaurado. Comparación lado a lado (código izq., Gemini der.) en `source/idle_compare.gif`.
- El usuario eligió el de Gemini: ya es `anims/idle` (`--pick 2,4,3,4 --fps 2`), atlas y bundle reexportados. El de código quedó en `source/idle_code.png/.json`. Probado en la demo del navegador: Penny parada con el idle nuevo, sin errores. Nota en `BIG_BANG.md`. Sin commit.

## 2026-11-01: repo para GitHub

**Qué se hizo**
- `git init` en `E:\ProyectosIA` (rama `main`). Un commit con identidad `tbittech <96559059+tbittech@users.noreply.github.com>`, solo en este repo.
- Archivos nuevos: `README.md`, `LICENSE` (MIT para el código; el arte es fan art no comercial, fuera de la MIT, con aviso de Warner/CBS) y `.gitignore`. Quedan afuera `.claude/`, `Assets BBTheory/referencias/` (fan art de otros artistas), `Assets BBad/themes/` y el estado del servidor.
- GitHub CLI instalado (`C:\Program Files\GitHub CLI\gh.exe`), logueado como tbittech. Repo público creado y subido: https://github.com/tbittech/living-4a-wallpaper (remote `origin`).

**Hipótesis vigentes**
- Los fondos (`backgrounds/*.jpg`) se generaron con IA. No está confirmado.

**Próximo paso**
- Si algún fondo se bajó de internet, sacarlo del repo. Cambios futuros: `git add -A && git commit && git push`.

## 2026-11-01: instalador portable

**Qué se hizo**
- `wallpaper/install.bat` (→ `scripts/install.ps1`): busca Python (ofrece winget si falta) e instala `aiohttp`. Pone los hooks con `scripts/hooks_setup.py` usando la ruta real de la carpeta y el python.exe completo, sin tocar los demás hooks (copia en `settings.json.bak-wallpaper`). Además crea la entrada de Lively (la ofrece por winget si falta; miniatura en `scripts/lively_thumbnail.jpg`), pone el servidor en Inicio y lo arranca.
- `wallpaper/uninstall.bat` (→ `scripts/uninstall.ps1`): deshace todo eso.
- `lively_mode.ps1` busca Lively.exe en Program Files o en LocalAppData. `install_startup.ps1` acepta `-Python`.
- Guía en `wallpaper/INSTALAR.md`. La prueba de la simulación quedó en `wallpaper/tools/sim_test.mjs` (`"clashes":0`).
- Probado con una copia movida a otra ruta (con espacios):
  - Los hooks apuntan a la ruta nueva; correrlo dos veces da lo mismo y desinstalar no deja rastro.
  - El servidor de la copia sirve la página y recibe el evento del hook.

**Hipótesis vigentes**
- `Lively.exe closewp -m -1` (en uninstall) no está probado.

**Descartado**
- Correrlo contra el settings.json real y el Lively de esta PC: ya andan con las rutas de `E:`.

**Próximo paso**
- Primera instalación real en otra PC: probar los winget (Python y Lively) y que Lively tome la entrada nueva.

## 2026-11-01: limpieza

Se borró de `Assets BBTheory/` y `wallpaper/` lo que no usa nada (copia completa en `D:\backupbbtheory`): `test_*.png` y `*_half.png`, los MP4/GIF de prueba de la raíz (`walk_sheldon*.gif`, `walk_leonard_*.mp4`, `flash_sheldon.mp4`, `frodo_leonard.mp4`, `effects_*.mp4`), `effects_preview.py`, `flash_preview.py`, `frodo_preview.py`, `walk_legs.py`, `characters/*/anims/*_x6.gif`, `characters/*/preview_x6.png`, las hojas repetidas fuera de `source/` (Leonard, Sheldon, `pennypennypenny/`), Sheldon `anims/walk_raw.png` y `anims/walk_back_orig.png`, `props/pizarron.jpg` y los `__pycache__`. El bundle exportado da idéntico al de antes y la demo de 30 min sigue con 0 choques. Las menciones a esos archivos más abajo son historia.

## 2026-11-01: entrada y salida por la esquina de adelante a la izquierda

**Qué se hizo**
- Lugar nuevo `exit` en `Assets BBTheory/theme.json` (casilla 16,30, la más a la izquierda del piso, delante del mueble del equipo de música; mira abajo-izq.). Sin puerta dibujada. Bundle reexportado.
- `character.js`: getter `outside` (`exit` si existe, si no `door`). Al abrir su programa (`session_start`) aparecen ahí mirando arriba-der. (`TURN` suma `down_left → up_right`); al cerrarlo (`session_end`) caminan hasta ahí, se despiden (`wave` + `LEAVE`/`BYE`) y se desvanecen; con el próximo evento vuelven a entrar por ahí. `door` solo lo usa Flash (`scenes.js`).
- Probado con `__sim` (`?demo=manual&debug=1`): Sheldon y Penny entran en 16,30, se van ahí con la despedida y el otro contesta. Sin captura (ventana oculta).

**Hipótesis vigentes**
- El «Chau» del que se queda sale ~1 s antes de que el otro desaparezca: casi no se ven juntos.

**Descartado**
- Dibujar una puerta real en la esquina (no hace falta).

**Próximo paso**
- Mirarlo en el fondo real (Lively) abriendo y cerrando Codex / Gemini CLI; si molesta, esperar a que terminen las respuestas `BYE` antes de desvanecerse.

## 2026-11-01: saludo al entrar y al irse

**Qué se hizo**
- Animación `wave` de Sheldon, Penny y Leonard (hojas de Gemini con el prompt universal `Assets BBTheory/PROMPT_SALUDO.md`, en `characters/<nombre>/source/wave.webp`), 10 cuadros de ida y vuelta a 6 fps (picks en `BIG_BANG.md` §5). Bundle reexportado.
- `character.js`: al terminar de aparecer (`greet = "enter"`) y al llegar a la puerta yéndose por `session_end` (`greet = "leave"`) llama a `chatter.greetTalk`. Con alguien en el living: frase (`ENTER` / `LEAVE`), saluda con la mano quieto (~1,7 s) y todos los presentes contestan de a uno (`GREET` / `BYE`; si el que contesta tiene otro globo espera hasta `chatter.reply_wait`, 4 s). Solo: comentario (`ENTER_ALONE` / `LEAVE_ALONE`), sin saludo. Al irse se queda lo que dura el globo y después desaparece. Irse a su pieza (`leave_after`) no saluda.
- Probado en el navegador con `__sim` (`?demo=1&debug=1`): entrar solo, con uno y con dos (contestan los dos), irse con otros y el último solo.

**Hipótesis vigentes**
- Algunas despedidas nombran a otro («Sheldon, portate bien.») aunque ya se haya ido.

**Próximo paso**
- Mirarlo en el fondo real abriendo y cerrando Codex / Gemini CLI.

## 2026-11-01: quién está lo deciden los procesos

**Qué se hizo**
- `wallpaper/server/procs.py`: cada 3 s (`config.json` → `processes`) mira los procesos. En Windows (psutil): `claude.exe` (app de Claude y Claude Code) → claude, `codex.exe` (app de Codex y CLI) → codex. En WSL, solo si ya hay distros prendidas (`wsl -l -q --running`, nunca prende una): `ps` adentro, un node que corre `.../gemini` → gemini (Gemini CLI desde bash), `.../codex` o el binario `codex` → codex. `gemini_debug_mcp.py` (MCP de Codex) no cuenta. ~0,5 s por pasada.
- `server.py`: `check_procs` abre la sesión `proc` del que tiene el programa abierto y, si falta 2 pasadas seguidas (`misses`), cierra **todas** sus sesiones (también las de hooks que quedaron colgadas) → `session_end` → se va por la puerta. Al arrancar hace una pasada antes de atender: con todo cerrado o recién prendida la compu, el living queda vacío aunque `.state.json` diga otra cosa.
- OmniRoute ya no hace entrar ni salir a nadie (`gateway_loop` solo manda `gateway_up/down` y borra las sesiones `omniroute` viejas). Los `call_logs` mueven a Leonard/Penny solo si su programa está abierto (sesión `proc`). Sin OmniRoute, Leonard y Penny se quedan paseando e interactuando con las escenas de reposo.
- Frontend: `leave_after: 0` = nadie se va a su pieza por estar quieto (`character.js`, `main.js`). La demo sigue con `demo_leave_after` (180).
- Probado: detección real (`python procs.py` → claude, codex, gemini), transiciones simuladas (arranque vacío, hook que cierra con Claude abierto, Gemini que se cierra a la segunda pasada). Servidor real reiniciado, Lively recargado con `lively_mode.ps1 live`.

**Hipótesis vigentes**
- El servidor lo arranca el hook de Claude: si después de prender la compu se abre solo Codex o Gemini, nadie aparece hasta que corra el servidor (falta `install_startup.ps1`).
- Gemini CLI en Windows (no WSL) se detecta por un node.exe que corre `gemini`: no probado.

**Próximo paso**
- Mirar el fondo cerrando Gemini CLI / Codex / Claude, uno por vez.

## 2026-11-01: Leonard y Penny siguen las requests de OmniRoute

**Qué se hizo**
- `wallpaper/server/calls.py` + `calls_loop` en `server.py`: cada `calls_every` (1 s) lee los `call_logs` nuevos de los dos últimos días (los que ya estaban al arrancar no se repiten; un JSON a medio escribir se reintenta 5 veces). Quién, por el path (`omniroute.clients`): `/v1/responses` → codex (Leonard), `:generateContent` / `:streamGenerateContent` → gemini (Penny); `/v1/messages` (Claude Code por OmniRoute) y `/api/...` se ignoran. Qué: si el input termina en la salida de una herramienta → `tool_call` con esa herramienta; si termina en un mensaje → `request_start`; status ≥ 400 → `error`. Sin requests en `idle` (20 s) → `turn_end`. Sesión siempre `omniroute`.
- Codex en code mode corre todo por `exec`: se saca la primera `tools.<nombre>(` del JS (exec_command, apply_patch, mcp__...). Gemini CLI llega guardado en formato OpenAI Chat (`messages`, rol `tool`). Solo viaja el nombre de la herramienta.
- `config.json`: `omniroute.call_logs/calls_every/idle/clients` y `tool_roles` nuevos (exec_command, write_stdin, run_shell_command, read_file, write_file, grep_search, google_web_search, js → web, ask_user...).
- Probado: el parser sobre los ~130 logs reales (exec_command, write_stdin, js, mcp__..., request_start) y un servidor de prueba en 8799 con logs falsos (mensaje → think, apply_patch → edit, run_shell_command de Gemini → shell, a medio escribir no rompe, turn_end a los idle s). Servidor real reiniciado (`gateway: true`). Las requests reales de hoy desde WSL: Codex dio **429** (límite de la cuenta), Gemini 200.

**Hipótesis vigentes**
- El log se escribe al terminar la request: el personaje va con unos segundos de atraso, y la herramienta que muestra es la que se acaba de correr (no la próxima).
- `error` no tiene reacción en el frontend todavía (solo los mantiene presentes).
- Si el health de OmniRoute falla un momento, `gateway_loop` cierra la sesión `omniroute` aunque haya requests.

**Descartado**
- Sacar la herramienta de la respuesta: OmniRoute la guarda streameada, con `content: None`.

**Próximo paso**
- Mirar el fondo mientras Codex/Gemini trabajan (Codex cuando se le pase el 429).
- ¿Reacción visual a `error` (429)?

## 2026-11-01: fondo sin servidor, Sheldon con Claude Code, Leonard y Penny con OmniRoute

**Qué se hizo**
- Lively en **modo live como archivo local** (`Type` 1, `FileName` = `wallpaper\public\index.html`): Lively lo sirve en un host virtual `*.localhost`, así el living (con su ciclo día/noche por la hora) se ve aunque `server.py` no esté. `main.js` se conecta a `config.json` → `server` (127.0.0.1:8765) cuando no lo sirve server.py, y reintenta solo. `lively_mode.ps1 live` ya lo deja así (con `-Debug1` sigue usando la URL). Verificado: el WebView de Lively conectado al servidor.
- `cc_hook.py`: si el servidor no está, lo **arranca** (pythonw, desprendido, marca `server/.starting` para no lanzar dos) y espera a que escuche; ~250 ms la primera vez. `session_end` no lo arranca.
- `server.py`: `.running.json` se escribe recién cuando el puerto escucha (antes un segundo servidor que no podía tomar el puerto borraba el archivo del primero y los hooks dejaban de mandar). Nuevo `gateway_loop`: cada 5 s pide `http://127.0.0.1:20128/api/health/ping`; si OmniRoute contesta, `codex` y `gemini` entran con sesión `omniroute` (Leonard, Penny), si no, la cierran. Config: `config.json` → `omniroute`. Probado con un health falso en 20128.
- OmniRoute: npm global `omniroute` v3.8.51 (se lanza a mano con `omniroute`, puerto 20128) y app Electron en `%LOCALAPPDATA%\Programs\OmniRoute`. Cada request queda en `~\.omniroute\call_logs\<fecha>\*.json` (Codex = `/v1/responses`; Gemini solo pasa por ahí con `omniroute run gemini`).
- `wallpaper/scripts/install_startup.ps1` (acceso directo del servidor en Inicio): **no se corrió**, lo bloqueó el permiso; lo tiene que correr el usuario.

**Hipótesis vigentes**
- Sin eventos, Leonard y Penny se van a su pieza a los `leave_after` (180 s) aunque OmniRoute siga prendido; para que reaccionen de verdad habría que leer `call_logs`.
- El servidor lanzado con `CREATE_BREAKAWAY_FROM_JOB` sobrevive al cerrar Claude Code (no probado).

**Descartado**
- Abrir la página con `file://` (los módulos ES y `fetch` no andan); no hace falta, Lively usa host virtual.

**Próximo paso**
- Usuario: correr `install_startup.ps1`, reiniciar y mirar el fondo; prender OmniRoute y ver a Leonard y Penny.
- Mirar `call_logs` de OmniRoute para mover a Leonard/Penny con requests reales.

## 2026-11-01: frases en el sofá y Flash/Hobbit cada 10 min

**Qué se hizo**
- `sim/chatter.js`: charla de sofá (`couchTalk`). Uno solo en el sofá → frase para sí (`SOLO`, por personaje); dos → frase y respuesta (`COUCH`, por pareja ordenada); tres (o un tercero yendo) → nada. Sentados ≥ 8 s, sorteo cada 15 s al 35 %, 60 s de pausa, 120 s por personaje para las de solo; sentados no giran al contestar (`face: false`). Config: `config.json` → `chatter.couch`.
- Flash y Hobbit: `cooldown` 2700 → 600 s, y `scenes.special_gap: 240` (respiro desde que termina una especial, la corten o no; `world.specialEnd` en `endScript`). Solo lo chequea `idleScenes`: las teclas F/H lo saltean.
- Probado con una simulación en node (1/2/3 en el sofá). Lively recargado con `setwp` (sigue en demo).

**Hipótesis vigentes**
- Con dos en asientos pegados los globos pueden taparse un poco (la respuesta sale mientras se ve la frase).

**Descartado**
- Nada nuevo.

**Próximo paso**
- Mirar en el fondo real los globos del sofá y el ritmo de las especiales.

## 2026-11-01: Sheldon juega a la Wii

**Qué se hizo**
- Animación `wii` de Sheldon (bowling, 16 cuadros de frente, 6 fps, loop): hoja de Gemini de 2×8 en `characters/Sheldon/source/wii.webp`, unida en una fila (`source/wii_row.png`) y extraída con `extract_anim.py` (celda forzada 2,42: la hoja vino chica).
- Las piernas salieron raras: lugar nuevo `tv` (casilla 10,40, detrás de la tele de los escritorios de adelante, `offset` 0,9), donde la capa `front_desks` las tapa y se ven la remera, las manos y el control.
- Wallpaper: guion `playWii` (`scenes.js`) y `Character.startWii`; `config.json` → `scenes.wii` (en reposo más de 60 s, 20 % cada 10 s, enfriamiento 10 min, 2 a 4 tiradas). Tecla **G** en la demo. Un evento lo corta. Bundle reexportado y Lively recargado (sigue en demo).

**Próximo paso**
- Mirarlo en el fondo real (no se pudo sacar captura del panel).

## 2026-11-01: hooks de Claude instalados (fase 3 cerrada)

**Qué se hizo**
- Hooks de `wallpaper/hooks/settings_snippet.json` fusionados en `%USERPROFILE%\.claude\settings.json` (agregados al lado de guard-logs y ctx-meter, sin pisarlos; backup `settings.json.bak-20261101-003341`).
- Probado con una sesión real: `/state` muestra `claude` presente, `working`, rol `shell` con la herramienta PowerShell.
- `wallpaper/scripts/lively_mode.ps1 live|demo [-Debug1]`: cambia la URL de la entrada de Lively y la vuelve a poner con `Lively.exe setwp`. Revisado solo que parsea, **no se corrió**.
- Lively **sin tocar**, todavía en demo (`?demo=1&sources=claude,codex,gemini`), porque el usuario está probando animaciones. La carpeta real es `Library\wallpapers\bbt_living4a\`.

**Hipótesis vigentes**
- `python` del PATH (3.10) alcanza para los hooks: con los de PowerShell ya funcionan.

**Descartado**
- Nada nuevo.

**Próximo paso**
- Cuando el usuario diga: `powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\lively_mode.ps1 live` y ver a Sheldon seguir a Claude en el fondo real (Leonard y Penny no aparecen sin OmniRoute).
- Fase 4: tarea de arranque del servidor.

## 2026-10-31 (noche): animaciones corregidas y wallpaper en Lively

**Qué se hizo**
- `type` de Sheldon y Leonard rehechas de frente (hojas nuevas de Gemini, `--pick 1,2,3,2`), centradas en la silla con el nuevo `shift` / `shift_by_character` de `extract_anim.py`; Leonard `lower` 10 → 24.
- Caminata de Sheldon (`walk`, `walk_back`) con paso: `Assets BBTheory/walk_cycle.py` arma zancada → paso → zancada opuesta → paso desde un solo cuadro, con piernas y brazos alternados (original en `anims/walk_orig.png`). `walk_back` ya no: hoja nueva de Gemini con la pierna de adelante alternando en cada cuadro (`source/walk_back_alt.png`, sacada de una captura: celda forzada, revisar si se ve blanda).
- Wallpaper en Lively con los tres: URL `http://127.0.0.1:8765/?demo=1&sources=claude,codex,gemini` (Leonard = codex, Penny = gemini).
- Fase 3 hecha por un agente: `wallpaper/server/` (aiohttp), `net.js`, `hooks/cc_hook.py`, `hooks/settings_snippet.json`. Probada con hooks simulados, no con una sesión real.
- Wallpaper puesto en Lively: entrada `Living 4A` en `%LOCALAPPDATA%\Lively Wallpaper\Library\wallpapersbt_living4a\`, por ahora en modo demo (ahora con los tres, ver arriba; antes `?demo=1&sources=claude`, Sheldon solo). Servidor corriendo con `pythonw wallpaper\server\server.py`.

**Hipótesis vigentes**
- Con zancada + paso alcanza para que la caminata no parezca deslizarse. La zancada opuesta sale por código: las piernas se espejan alrededor de la cadera y los zapatos se trasladan sin espejar (así siguen apuntando para adelante). Los brazos se balancean desde el hombro, opuestos a la pierna de adelante, y en el paso quedan al costado. Gemini no supo hacer la hoja alternada, ni con referencia de poses.

**Descartado**
- Armar la zancada con la otra pierna moviendo o espejando las piernas (rompe el dibujo, los zapatos quedan al revés).

**Próximo paso**
- Seguir corrigiendo animaciones (¿mismo ciclo de caminata para Leonard y Penny?).
- Instalar los hooks en el settings.json real y pasar Lively a `http://127.0.0.1:8765/` (sin `?demo`) para que Sheldon siga a Claude.
- Fase 4: tarea de arranque del servidor (hoy, si se reinicia Windows hay que lanzarlo a mano).


## 2026-10-31

**Qué se hizo**
- Breaking Bad (`Assets BBad/themes/breaking_bad/`): fondos alineados, zona caminable y 5 lugares marcados, escala ×4 probada, sprites de referencia de Walter y Jesse con atlas.
- Herramientas en `Assets BBad/tools/`: `align_backgrounds`, `extract_sheet`, `extract_anim` (hoja de animación → atlas, probado con hojas sintéticas: idéntico al píxel), `compose_scene` y `theme.py`.
- El proyecto pasó a **temas intercambiables**: roles genéricos (`entry`, `shell`, `edit`, `read`, `web`, `think`, `rest`, `scene`) mapeados por cada tema a sus lugares y animaciones en `theme.json`. Refactor verificado: mismos resultados al píxel.
- Cambio de tema a **Big Bang Theory**, en su propia carpeta `Assets BBTheory/` (las herramientas la encuentran por `Assets BBad/config.json` → `theme_paths`). Documento: `Assets BBTheory/BIG_BANG.md`. Referencias guardadas en `Assets BBTheory/referencias/`.
- Sprites de referencia de **Sheldon, Leonard y Penny** extraídos de las hojas de Gemini (`Assets BBTheory/characters/<nombre>/`): 4 vistas a ~38×112 nativo. `extract_sheet.py` ganó `--order` (estas hojas traen frente, 3/4, espalda, perfil) y ahora detecta píxeles de hasta 4 px (estas hojas tienen la mitad de resolución que las de la van); Walter re-extraído sale idéntico al píxel.

- Fondos de Big Bang (día, noche sin agentes, noche con agentes; isométricos) cableados en `theme.json` y alineados a 1372×764 en `Assets BBTheory/aligned/`.
- **Grilla de casillas marcada** sobre el living (sigue las baldosas, ~42×21 px): 155 casillas caminables conectadas con la puerta y 7 lugares (casilla + dirección), todos alcanzables. Nuevo `Assets BBad/tools/grid.py` (grilla, camino más corto, vista por dirección); `theme.py` y `compose_scene.py` aceptan lugares en casillas sin romper la van (probado). Marcado reproducible con `Assets BBTheory/mark_grid.py`; prueba en `Assets BBTheory/test_grid.png`.
- **Piso entero caminable**: el borde del piso sigue la base de las paredes y los muebles bloquean solo su huella (281 casillas, antes 155). **Asientos**: tres en el sillón y las dos sillas de las compus, agrupados (`scene.seats`) con dueño (`scene.owners`): Sheldon silla derecha y (cambiado después) `couch_right`, Leonard silla izquierda. `theme.py` (`place_key`) y `compose_scene.py` reparten el asiento por personaje; la van sigue igual.
- **Primeras animaciones reales**: Sheldon `walk` y `walk_back` desde hojas de Gemini (primera prueba real de `extract_anim.py`: altura y pies bien a la primera). `extract_anim.py` ahora nunca guarda como color nuevo un tono magenta (borde contaminado por el fondo). Nuevo `walk_preview.py`: GIF del personaje caminando por la grilla entre dos lugares.
- **Capa de primer plano**: muebles recortados de los fondos (GrabCut sobre un polígono aproximado + borrado del piso pegado), con huella en casillas; `layers.py` decide qué mueble tapa a quién. Ya se puede caminar detrás del sillón, la columna, la isla y los escritorios.
- **Pizarrón con atril** agregado como objeto (`scene.props`): entre el sillón individual y la isla, como en la referencia; el lugar `whiteboard` pasó a estar delante (antes era la hoja pegada junto a la puerta).
- Sheldon `idle` y `sit`. Gemini mezcló vistas (frente y 3/4) en la misma hoja: `extract_anim.py --pick 2,2,4,2` elige qué cuadros usar y en qué orden. También `--height` / `animations.X.height` para animaciones más bajas, pero sentado Gemini lo dibuja con la misma cabeza y la misma altura, así que no hizo falta. `compose_scene.py` acepta una animación como vista (`Sheldon@couch:sit`); `walk_preview.py` termina con `sit` o `idle`. Lugares con `offset` en píxeles (sillas de las compus).
- Sheldon `type` (sentado en la compu; la hoja vino a la mitad de resolución y sale un poco más blanda, `--pick 2,3,4,3`, `lower: 18` para apoyar el teclado) y `write` (de espaldas en el pizarrón, salió bien a la primera). `walk_preview.py --anim` elige la animación al llegar.
- Sheldon `think` (de espaldas en el pizarrón, marcador en el mentón) y `read` (cómic en el sillón, `--pick 2,2,3,4`). Sheldon tiene animación para todos sus roles.
- **Escena especial Sheldon Flash**: personaje `sheldon_flash` (referencia + pose + correr de frente y de espaldas), estela de clones difuminados por código y `flash_preview.py` con la escena entera en MP4. `extract_sheet.py` ganó `--height` (igualar altura a otro personaje) y limpieza del borde magenta. `walk_preview.py` quedó en piezas reutilizables (`walk_steps`, `hold`, `with_trail`, `save_gif` que también guarda MP4).

- Leonard (todas sus animaciones, `write`/`look` provisorias), Penny (todas menos `look`) y Leonard hobbit hechos (detalle en `BIG_BANG.md` §8).
- **Escena especial Leonard es Frodo**: pasillo a los cuartos marcado (`hallway`, 6 casillas nuevas bajo la ventana de la derecha, 286 en total; `mark_grid.py` ya no borra `scene.effects` al regenerar) y la heladerita verde como capa (`cut_layers.py` acepta nombres de muebles para recortar solo esos; verificado que el recorte es determinista y las demás capas quedaron iguales). `frodo_preview.py` → `frodo_leonard.mp4`: tramado, chispas, destello del Anillo, tinte gris y reapariciones en casillas visibles.
- **Plan del wallpaper en vivo** en [WALLPAPER.md](WALLPAPER.md) (hecho con un agente de planificación): Canvas 2D en JS plano + servidor Python/aiohttp, `export_bundle.py` que reusa el pipeline, simulación con director de escenas, hooks de Claude Code, Lively y fases.

- **Wallpaper fase 1** (`wallpaper/`): `export_bundle.py` arma el bundle desde el tema (fondos con props, 17 capas, grilla con los pies precalculados, lugares, atlas de los 5 personajes); frontend en JS plano sin build (`grid.js` y `layers.js` portados de Python, escalado sharp-bilinear, máquina de estados, simulador con teclas). Probado en el navegador (entrar, sillón, pizarrón, compu, ventana, irse al pasillo y volver) y 20 min simulados en Node con los tres personajes: 0 choques, nadie trabado.

- **Wallpaper fase 2**: efectos por código portados a JS con el mismo azar que Python (las 4 escenas de referencia dan 0 píxeles distintos), paseo en reposo, esperas en lugares ocupados, globos de diálogo, guiones (`scenes.js`). Adelantado de las fases 5 y 6: **disputa por el sillón** (Sheldon dueño de `couch_right`, Penny lo prefiere; «Penny... ese es mi lugar.») y **Sheldon Flash** con estela, cortable por eventos. Probado en Node (disputa, Flash completo, cortado antes y con el traje, 30 min con los tres) y en el navegador.

- **`type` de frente** para Sheldon y Leonard (antes de 3/4 con teclado flotante): hojas nuevas, `--pick 1,2,3,2` en los dos, bundle reexportado. Probado en el wallpaper: los dos tecleando en sus compus, el escritorio tapa las piernas. Estaban 10 px a la derecha de la silla: nuevo `shift` / `shift_by_character` en `extract_anim.py` y `theme.json` (como `lower`, pero en x), los dos centrados. Leonard además flotaba sobre el escritorio: `lower` 10 → 24.
- **Caminata de Sheldon con paso**: las hojas traían la misma zancada en los 4 cuadros (un pie quieto, se deslizaba). Nuevo `Assets BBTheory/walk_cycle.py`: separa las piernas de un cuadro y arma zancada → paso (el pie de atrás se adelanta, el cuerpo sube 1 px) → zancada → paso, para `walk` y `walk_back`, sin hoja nueva. Cambiar las piernas para la otra zancada (moviéndolas o espejándolas) rompía el dibujo: descartado (resuelto después: espejo de piernas con los zapatos trasladados, ver arriba). Prueba: `walk_sheldon_desk.gif`; bundle reexportado.

- **Wallpaper fase 3**: servidor `wallpaper/server/server.py` (aiohttp, solo 127.0.0.1: estáticos, `/ws` con snapshot y eventos, `/event` que descarta todo texto libre, `/state`; el estado se guarda y sobrevive a un reinicio), `net.js` con reconexión (al cargar, el que ya estaba trabajando aparece directo en su lugar) y hook `cc_hook.py` (~85 ms, sin salida, siempre exit 0; solo tipo, herramienta, id de sesión y hora). Probado con hooks simulados y en el navegador: Sheldon va a la compu, al sillón y se va por la puerta; matar y reiniciar el servidor reconecta sin moverlo. Falta pegar `wallpaper/hooks/settings_snippet.json` en el settings.json real.

- **Wallpaper en Lively** (adelanto de la fase 4): entrada `Living 4A` (URL `http://127.0.0.1:8765/`) puesta como fondo, servidor corriendo con `pythonw` y el WebView de Lively conectado. Falta: hooks en el settings.json real y la tarea de arranque (si se reinicia Windows, lanzar el servidor a mano).

**Decidido**
- `look` de Penny queda para después.
- El lugar de Sheldon en el sillón es `couch_right` (antes `couch_left`) y Penny también lo prefiere: se sienta ahí si está libre y Sheldon la hace mover. Solo Sheldon reclama su asiento (`disputes`).
- Wallpaper: `config.json` vive en `wallpaper/public/` (lo lee el frontend). Sin eventos un rato, Sheldon y Leonard se van al pasillo y vuelven por ahí; al cerrar la sesión se van por la puerta.
- Escenario **isométrico con lógica de movimiento tipo Habbo**: piso en casillas, caminar de casilla en casilla en 4 direcciones diagonales, una persona por casilla, lugares = casilla + dirección. Alcanza con las vistas 3/4 de frente y 3/4 de espalda, espejadas.
- Reparto: Claude = Sheldon, Codex = Leonard, Gemini = Penny.
- Personajes menos chibi que en la van (como salieron las hojas, ~38×112 nativo), `sprite_scale` 1 sobre el fondo alineado: quedan de la altura de la puerta.

**Hipótesis vigentes**
- Sillón = `rest`, pizarrón = `edit`/`think`, escritorio = `shell`, telescopio = `web`; conflicto por archivo = disputa por el lugar en el sillón.

**Descartado**
- Breaking Bad como tema principal (queda en pausa, no se borró).
- ×5 de escala en la van (más altos que la puerta).
- Peleas físicas en Big Bang.

**Próximo paso**
- Wallpaper, fase 3 de `WALLPAPER.md`: servidor (aiohttp) + hook de Claude Code, para que Sheldon se mueva con sesiones reales. Después, Frodo en vivo (su escena ya está hecha offline).
- Pendiente general: claude-office y OmniRoute sin revisar; preguntas abiertas de `WALLPAPER.md` §8 (resolución del monitor, ciclo día/noche).
