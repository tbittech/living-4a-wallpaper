# Escena de IAs: idea y lógica de animación

Fondo de pantalla animado en pixel art: un escenario en corte lateral donde cada IA que trabaja es un personaje.
Cuando una IA está activa, su personaje entra a la escena y se anima según lo que está haciendo.

El escenario y los personajes son **temas intercambiables**: la lógica (estados, roles, interacciones, conexión) es la misma, y cada tema pone su fondo, sus lugares y su reparto.

Base: fork de **claude-office** (visualización en pixel art de Claude Code). Se reemplaza la oficina por el escenario del tema y se suman más agentes.
La conexión de datos está en [CONEXION.md](CONEXION.md).

---

## 1. Temas

| Tema | Carpeta | Estado |
|---|---|---|
| Big Bang: el departamento 4A | `../Assets BBTheory/` (vía `theme_paths`) | **activo en diseño**, faltan todos los assets ([BIG_BANG.md](../Assets%20BBTheory/BIG_BANG.md)) |
| Breaking Bad: la van | `themes/breaking_bad/` | fondos, Walter y Jesse hechos; en pausa ([TEMA.md](themes/breaking_bad/TEMA.md)) |

El tema activo se elige en `config.json` (`"theme": "..."`). Todas las herramientas aceptan `--theme NOMBRE` para usar otro sin tocarlo.
Mientras Big Bang no tenga fondos, `config.json` sigue apuntando a `breaking_bad`.

### Estructura de un tema

```
themes/<tema>/
  theme.json            todo lo que define al tema (ver abajo)
  TEMA.md               reparto, notas y pendientes del tema
  backgrounds/          fondos originales (día, noche sin agentes, noche con agentes)
  aligned/              fondos alineados + alignment.json (los genera align_backgrounds.py)
  characters/<nombre>/
    source/             hoja de referencia original (4 vistas sobre magenta)
    front / three_quarter / side / back .png, sheet.png, preview_x6.png, meta.json
    anims/              tiras de cada animación (.png, .json, _x6.gif)
    atlas.png + atlas.json
  test_scene*.png       escenas de prueba
```

### `theme.json`

| Clave | Qué define |
|---|---|
| `backgrounds` | Archivo de cada estado del fondo (`day`, `night_idle`, `night_active`), cuál es la referencia para alinear y `align_box`: la zona que tiene que quedar fija, en fracciones de la imagen (`null` = toda). |
| `scene` | `sprite_scale` (escala entera de los sprites sobre el fondo alineado), `walkable` (polígono del piso) y `places` (lugares con nombre propio del tema: `lab_table`, `couch`…, en píxeles, donde van los pies). |
| `roles` | Lo que hace el agente, en términos genéricos, mapeado a un lugar del tema y una animación (ver §5). |
| `animations` | Catálogo de animaciones del tema: cuadros, fps y loop. |
| `cast` | Qué personaje es cada IA (`claude`, `codex`, `gemini`). |

**Roles genéricos:** `entry` (entrar/salir), `shell` (comandos), `edit` (editar archivos), `read` (leer/buscar), `web` (búsqueda externa), `think` (esperando al modelo), `rest` (reposo), `scene` (lugar de discusiones y peleas).
La lógica y el frontend solo conocen los roles; cada tema decide dónde queda cada uno y con qué animación.

### Armar un tema nuevo

1. Crear `themes/<tema>/theme.json` (copiar uno existente) y poner los fondos en `backgrounds/`.
2. `align_backgrounds.py --theme <tema>`. Si tiembla, ajustar `align_box` a la zona del escenario y repetir.
3. Marcar `walkable` y `places` sobre `aligned/day.png`; probar con `compose_scene.py --debug`.
4. Por personaje: `extract_sheet.py` con su hoja de referencia, probar la escala en la escena y después las animaciones con `extract_anim.py`.

---

## 2. Herramientas (`tools/`)

Todas se corren desde `E:\ProyectosIA` con `python -I "Assets BBad/tools/<script>.py" ...` y aceptan `--theme`.

| Script | Qué hace |
|---|---|
| `theme.py` | Módulo común: carga el tema activo, rutas, lugares y roles. |
| `align_backgrounds.py` | Alinea los fondos a la referencia del tema (SIFT + RANSAC con similitud, refinado con ECC sobre los bordes, solo dentro de `align_box`) y los recorta al rectángulo común. `--debug <carpeta>` guarda superposiciones para revisar. |
| `extract_sheet.py HOJA NOMBRE` | Hoja de referencia (4 vistas) → sprites nativos del personaje. Copia la hoja a `source/`. |
| `extract_anim.py HOJA NOMBRE ANIM` | Hoja de animación → cuadros nativos y atlas (ver §4). `--rebuild NOMBRE` solo rearma el atlas. |
| `compose_scene.py nombre@lugar ...` | Escena de prueba sobre el fondo alineado. El lugar puede ser un lugar del tema, un rol (`shell`, `rest`…) o `x,y`; `:left` espeja y `--debug` dibuja el piso y los lugares. |

Los fondos generados por IA nunca coinciden al píxel entre día y noche (en la van había hasta ~15 px de diferencia en los bordes): **usar siempre `aligned/`**, nunca los originales.

---

## 3. Escena y estados del fondo

| Estado | Cuándo |
|---|---|
| `day` | Horario diurno (opcional, ciclo según la hora real) |
| `night_idle` | De noche, sin agentes activos |
| `night_active` | De noche, con al menos un agente activo |

- Transiciones por **fundido** (crossfade) de 1–2 s entre las imágenes alineadas.
- De día "activo" no cambia el fondo: se nota por los personajes y los efectos.

### Capas de dibujo (de atrás hacia adelante)

1. Cielo o exterior (lo que se ve por las ventanas, si el tema lo anima)
2. Fondo de la escena (imagen alineada)
3. Efectos del escenario (los define cada tema)
4. **Personajes**, ordenados por la coordenada Y de los pies (el que está más abajo se dibuja adelante, como en los beat 'em up)
5. Primer plano opcional (marcos de puertas, respaldo del sillón… para pasar "por detrás")
6. Efectos encima (polvo, estrellitas, "!" y "?", globos de diálogo)

---

## 4. Especificación de los sprites

- **Estilo:** chibi *super-deformed* de baja resolución, no realista.
  Cabeza enorme (~la mitad de la altura total), cuerpo y piernas cortitos, contorno oscuro grueso de 1 px nativo, paleta limitada, sombreado de 2–3 tonos.
  Resolución nativa chica (~32×58 por personaje) y escalado entero por código (`sprite_scale` del tema), así los píxeles quedan gruesos y nítidos.
  Los generadores devuelven "píxeles falsos" con una grilla despareja: al procesar se detecta la grilla y se reduce a la resolución nativa real.
- **Hoja de referencia por personaje:** 4 vistas (frente, 3/4 a la derecha, costado a la derecha, espalda). Es la imagen oficial y se adjunta en todos los prompts.
- **Hojas de animación:** una fila horizontal de N cuadros por imagen, cuadros de ~64×64, fondo magenta sólido `#FF00FF`.
- Mirando a la izquierda: no se genera, se espeja por código.

### Procesamiento de animaciones (`extract_anim.py`)

1. Quitar el magenta → transparencia.
2. Detectar la grilla de píxeles falsos y reducir a resolución nativa. Si la altura del cuadro más alto no coincide con la referencia (±8 %), avisa y fuerza la celda que la iguala. En ese caso conviene revisar el resultado o regenerar la hoja.
3. Separar los cuadros por columnas vacías (si están pegados, corta en partes iguales).
4. Paleta: k-means y después cada color al más cercano de la hoja de referencia (todas las animaciones comparten paleta). Los colores que quedan lejos (ropa nueva, objetos) se conservan, hasta `--extra-colors` (8 por defecto).
5. Limpiar píxeles sueltos y agujeros de 1 px.
6. Alinear por los pies: cada cuadro apoyado en el piso y centrado en las piernas (el cuarto inferior), así un brazo estirado no corre el cuadro. Con `--keep-y` respeta saltos y caídas.
7. Exportar `anims/<anim>.png|.json|_x6.gif` y rearmar `atlas.png` + `atlas.json`.

Cuadros, fps y loop salen de `animations` en `theme.json` (`--frames`, `--fps`, `--loop/--no-loop` para cambiarlos).

**`atlas.json`:** `scale` del tema y una entrada por animación con `fps`, `loop`, `anchor` (píxel de los pies dentro del cuadro) y `frames` ([x, y, ancho, alto] en el atlas).
Incluye las 4 vistas de referencia como `ref_front`, `ref_three_quarter`, `ref_side` y `ref_back`, así el frontend puede arrancar antes de que existan las animaciones.
Para dibujar: `pos_pantalla = punto_de_pies − anchor × escala`.

Probado con hojas sintéticas imitando a Gemini (píxeles falsos de 21,7 px, cuadros desparejos, JPEG): el cuadro sale idéntico al píxel al sprite original. Falta probarlo con una hoja real de Gemini.

### Animaciones comunes a todos los temas

`idle`, `walk`, `think`, `celebrate` y `argue` las usa la lógica general. Las de trabajo (`cook`, `type`, `sit`…) las nombra cada tema en `roles`.

---

## 5. Máquina de estados de cada personaje

```
          (agente aparece)
 ABSENT ──────────────────► ENTERING ──► IDLE
   ▲                                      │ ▲
   │ (timeout sin actividad)              │ │ (turno terminado)
 LEAVING ◄────────────────────────────────┘ │
                                            │
 IDLE ── request_start ──► THINKING ── tool_call ──► WORKING(tool)
                              ▲                          │
                              └──── tool_result ─────────┘
 THINKING / WORKING ── turn_end ──► CELEBRATE (si fue largo) ──► IDLE
 cualquier estado ── error ──► (ver interacciones)
```

- `ENTERING`: aparece en el lugar del rol `entry` y camina con `walk` hasta el de `rest`.
- `THINKING`: rol `think`. `IDLE`: rol `rest`.
- `WORKING(tool)`: camina al lugar del rol de la herramienta y reproduce su animación.
- `LEAVING`: tras **N minutos** sin eventos (configurable, ~3 min) camina a `entry` y desaparece.
- Las animaciones que no hacen loop (`celebrate`, `punch`…) bloquean el cambio de estado hasta terminar, pero los eventos que llegan mientras tanto se encolan, no se pierden.

### Herramienta → rol

| Herramienta (por nombre, sin importar el agente) | Rol |
|---|---|
| bash, shell, exec, run_command | `shell` |
| edit, write, apply_patch, replace | `edit` |
| read, grep, glob, list, search_files | `read` |
| web_search, web_fetch | `web` |
| subagentes / task | `think` + globo con 📞 |
| desconocida | `edit` |

La lista exacta de nombres se completa cuando veamos qué herramientas manda cada CLI (ver [CONEXION.md](CONEXION.md)).

---

## 6. Interacciones entre personajes

Escenas cortas (2–6 s) que toman el control de 2 personajes y después los devuelven a su estado normal.
Se arman combinando poses dibujadas con movimiento por código (acercarse, sacudón de pantalla, polvo, salir despedido).
Los disparadores son comunes; la escena concreta la pone cada tema (ver su `TEMA.md`).

| Disparador | Idea general |
|---|---|
| Dos agentes activos a la vez por más de X segundos | Discusión: se miran y aparecen globos con "!" y "?" |
| Dos agentes tocan **el mismo archivo** (por las rutas de las herramientas) | Conflicto fuerte (pelea, disputa por un lugar…) |
| Un agente recibe un error del proveedor (429 / 5xx) | El otro se burla; el afectado se enoja |
| El combo de OmniRoute cambia a un proveedor de respaldo | El afectado sale, "cambia de ropa" y vuelve a entrar |
| Un agente termina un turno largo sin errores | `celebrate`; si hay otro presente, festejan juntos |

Reglas para que no sea molesto:
- **Enfriamiento** por escena (por ejemplo, máximo una pelea cada 10 minutos).
- Probabilidad, no certeza: algunas escenas salen al 30–50 % de las veces para que no sea repetitivo.
- Nunca interrumpir una escena con otra.

---

## 7. Efectos por código (sin video)

Todos en loop perfecto y con píxeles nítidos (escalado entero, sin suavizado). Cada tema lista los suyos en su `TEMA.md`.
Comunes: luz que parpadea cada tanto, algo que se mueve por la ventana, partículas cuando alguien trabaja.

---

## 8. Como fondo de pantalla

- Se muestra con **Lively Wallpaper** apuntando a la URL local del frontend.
- Lively pausa el fondo con apps a pantalla completa.
- Respetar las zonas de los íconos del escritorio y de la barra de tareas.
- El frontend se reconecta solo si el servidor se reinicia.
- Mostrar a ~30 FPS como máximo; el pixel art no necesita más.

---

## 9. Plantillas de prompt para Gemini

**Hoja de referencia:** adjuntar el fondo de día del tema y la hoja de otro personaje ya hecho para igualar escala y estilo.

**Animación** (adjuntar la hoja de referencia del personaje):

```
Pixel art sprite sheet, 4 frames in a single horizontal row, each frame 64x64 pixels,
same character in every frame matching the attached reference exactly
(same face, clothes, colors, proportions). 3/4 view facing right.
Animation: [ACCIÓN].
Solid flat magenta background (#FF00FF), no shadows on the background,
no text, no borders, even spacing between frames, character feet aligned
on the same baseline in every frame.
```

Checklist al recibir cada hoja: mismo personaje en todos los cuadros, 4 cuadros separados, fondo magenta parejo, sin texto.
