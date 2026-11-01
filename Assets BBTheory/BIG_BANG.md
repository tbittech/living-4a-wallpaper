# Big Bang: el departamento 4A

Tema de la escena de IAs ambientado en el living de Sheldon y Leonard. Cada IA activa es un personaje chibi que entra al departamento y se anima según lo que hace.
Lo general (estados, roles, procesamiento de sprites, conexión) está en [IDEA_Y_ANIMACION.md](../Assets%20BBad/IDEA_Y_ANIMACION.md) y [CONEXION.md](../Assets%20BBad/CONEXION.md); las herramientas están en `Assets BBad/tools/` y encuentran este tema por `config.json` → `theme_paths`.

---

## 1. Carpetas

```
Assets BBTheory/
  BIG_BANG.md          este documento
  theme.json           fondos, escena, roles, animaciones y reparto (lo leen las herramientas)
  referencias/         imágenes de inspiración (no se usan como assets)
    living_isometrico_calgonzales.png   living isométrico (fan art de otro artista)
    chibis_lateral_bonkar.png           estilo de personaje chibi buscado
  backgrounds/         fondos: solcito.jpg (día), solitario-spider.jpg (noche sin agentes), noche-con-amigos.jpg (noche con agentes)
  aligned/             los tres alineados a 1372×764 + alignment.json
  aligned/             fondos alineados (los genera align_backgrounds.py)
  characters/<nombre>/ source/ (hoja de referencia) + sprites, anims/ y atlas
  props/               whiteboard.png (el pizarrón) y pizarron_src.png (su imagen de Gemini)
  *.py                 pasos del pipeline propios del tema: mark_grid, cut_layers, blanket_sheet, walk_cycle, walk_from_leonard, walk_arms
```

> **Limpieza (2026-11-01):** se borraron las salidas de prueba (`test_*.png`, los MP4/GIF de la raíz, `anims/*_x6.gif`, `preview_x6.png`), los prototipos `effects_preview.py`, `flash_preview.py`, `frodo_preview.py` y `walk_legs.py` (la caminata de 8 cuadros, reemplazada por `walk_from_leonard.py`), copias repetidas de hojas y `props/pizarron.jpg`. Están en `D:\backupbbtheory`. Las herramientas de `Assets BBad/tools/` vuelven a generar `test_*.png`, `*_x6.gif` y `preview_x6.png` cuando se corren. Donde abajo se nombra un archivo borrado es historia: la escena en vivo es la de `wallpaper/` (WALLPAPER.md).

Comandos (desde `E:\ProyectosIA`), siempre con `--theme big_bang` mientras `config.json` apunte a la van:

```
python -I "Assets BBad/tools/align_backgrounds.py" --theme big_bang
python -I "Assets BBad/tools/extract_sheet.py" HOJA.jpg sheldon --theme big_bang
python -I "Assets BBad/tools/extract_anim.py" HOJA.png sheldon walk --theme big_bang
python -I "Assets BBad/tools/compose_scene.py" sheldon@couch leonard@desk --theme big_bang --debug
```

---

## 2. Estilo

### Personajes: chibi
Como en `referencias/chibis_lateral_bonkar.png` y los de la van:
- Cabeza enorme (~la mitad de la altura), cuerpo y piernas cortitos, contorno oscuro de 1 px nativo, paleta corta, 2–3 tonos de sombra.
- Menos chibi que en la van (cabeza ~un tercio del cuerpo): confirmado que así está bien.
- Resolución nativa ~38×112 (lo que dieron las hojas de Sheldon, Leonard y Penny) Sobre el fondo alineado (1372×764) van a escala ×1: quedan de la altura de la puerta y la heladera (probado). Para la pantalla se escala la escena entera.
- Las hojas de Gemini de este tema traen las vistas en orden frente, 3/4, espalda, perfil: `extract_sheet.py ... --order front,three_quarter,back,side`.
- Rasgos que los identifican a esta escala: **Sheldon** remera de superhéroe sobre manga larga, flaco y alto; **Leonard** anteojos gruesos, buzo con capucha, pelo oscuro; **Howard** flequillo, pantalón ajustado, cinturón con hebilla grande; **Raj** pelo con raya, chaleco tipo sweater; **Penny** pelo rubio, ropa de Cheesecake Factory.

### Escenario: isométrico, con lógica tipo Habbo
Decidido: el living se dibuja **isométrico** y los personajes se mueven como en un juego de habitaciones isométricas por casillas (estilo Habbo). Solo se toma la lógica de movimiento; el arte es propio.

- **Piso en casillas** (rombos 2:1). Cada lugar (`couch`, `desk`, ...) es una casilla más la dirección a la que mira el personaje ahí.
- **Se camina de casilla en casilla** y solo por los dos ejes del piso, o sea en 4 direcciones de pantalla (abajo-derecha, abajo-izquierda, arriba-derecha, arriba-izquierda). El camino se busca por la grilla esquivando muebles y casillas ocupadas.
- **Vistas que hacen falta:** 3/4 de frente (abajo-derecha) y 3/4 de espalda (arriba-derecha); las de la izquierda salen espejando. Las hojas actuales ya traen las dos (`three_quarter` y `back`); `front` y `side` quedan para poses de cámara o de perfil.
- **Una persona por casilla.** Los asientos del sillón son casillas con dirección fija; la disputa por el lugar de Sheldon es una disputa por esa casilla.
- **Orden de dibujo** por profundidad de casilla (fila + columna), con los muebles altos partidos en piezas si hace falta que alguien pase por detrás.
- **Marcado** (`mark_grid.py`, guarda en `theme.json`): la grilla sigue las baldosas del piso (~42×21 px, una casilla por personaje). El piso va hasta la base de las paredes y el frente de la mesada; los muebles bloquean solo su huella en el piso, así que se camina todo el piso libre (detrás del sillón, la cocina, el rincón del telescopio y la franja delante de los escritorios, el pasillo a los cuartos): 286 casillas, todas conectadas con la puerta. `Assets BBad/tools/grid.py` tiene la grilla, el camino más corto y la vista de cada dirección; `compose_scene.py --debug` dibuja las casillas.
- **Asientos:** el sillón tiene tres (`couch_left`, `couch_mid`, `couch_right`, uno por almohadón) y hay dos sillas de compu (`desk_left`, `desk_right`). En `scene.seats` se agrupan como `couch` y `desk`, y `scene.owners` dice de quién es cada uno: Sheldon `couch_right` y la silla de la derecha, Leonard la silla de la izquierda. `scene.prefers` dice qué asientos ajenos le gustan a alguien: Penny también se sienta en `couch_right` si está libre. Un rol que apunta a un grupo lleva al personaje a su asiento, si no al que prefiere, si no al primero libre sin dueño, si no al primero libre (`theme.py` → `place_key`; igual en el wallpaper). En el wallpaper, si Sheldon encuentra a alguien en su lugar le dice «Penny... ese es mi lugar.» y el otro se cambia (§6). Las sillas de las compus tienen `offset`: los pies van debajo del escritorio (lo tapa la capa) y se ve el torso sobre la mesa. Los asientos del sillón también tienen `offset` (`couch_left` 6,11, `couch_mid` 0,16, `couch_right` 0,19): `sit`/`read` se anclan por los pies, así que el lugar se baja hasta que las rodillas (~28-31 px sobre los pies) caen en el borde delantero del almohadón y las piernas cuelgan por delante; `couch_left` va 6 px a la derecha para quedar sobre el almohadón y no sobre el apoyabrazos. Con los pies en el piso, la mesa ratona tapa en parte los zapatos de quien está en `couch_right` (está delante).
- **Capa de primer plano** (`cut_layers.py`, después de `mark_grid.py`): sillón, sillón individual, mesas, columna, isla, banqueta, escritorios, sillas, percheros y ADN recortados de los tres fondos en `aligned/layers/<fondo>/`, con su huella en casillas (`scene.layers`). `Assets BBad/tools/layers.py` los redibuja encima de quien queda detrás (casilla con la huella más cerca de la cámara en los dos ejes); sentado en un asiento del mueble se ve delante. Lo usan `compose_scene.py` y `walk_preview.py`.
- **Objetos agregados** (`scene.props`, se marcan en `mark_grid.py`): cosas que no están en el fondo, como el pizarrón con atril (`props/whiteboard.png`, reducido de `props/pizarron_src.png`, la imagen de Gemini). Se pintan sobre el fondo (de noche, oscurecidos según cuánto cambia el fondo alrededor), bloquean su casilla y tapan a quien pasa por detrás como cualquier capa.

La referencia del living es fan art de otro artista (marca de agua de Behance): sirve de inspiración para la distribución, pero el fondo se genera de cero y no se copia esa imagen.

---|---|---|
| **Isométrico** (como la referencia del living) | Muy lindo, piso profundo, el sillón se lee perfecto, el orden por Y funciona de verdad | Caminar en diagonal necesita dos vistas por animación de caminata: 3/4 de frente (abajo-derecha, espejada abajo-izquierda) y 3/4 de espalda (arriba) |
| **Corte lateral** (como la van) | Todo el pipeline ya probado tal cual; solo vistas de 3/4 de frente | Piso poco profundo, menos espacio para 3–5 personajes |

Recomendación: **isométrico**, solo hace falta sumar `walk_back` (y quizás `idle_back`). El resto de las animaciones se hacen mirando a cámara.
La referencia del living es fan art de otro artista (marca de agua de Behance): sirve de inspiración para la distribución, pero el fondo se genera de cero y no se copia esa imagen.

---

## 3. Reparto (confirmado)

| IA | Personaje |
|---|---|
| Claude Code | Sheldon |
| Codex (vía OmniRoute) | Leonard |
| Gemini CLI | Penny |

Sobran personajes (Howard, Raj, Amy, Bernadette) para sumar más IAs.

---

## 4. Lugares y roles

En `theme.json` → `scene.places`, como casilla + dirección. Los que están sobre un mueble (sillón, silla, banqueta) no se pisan al caminar: son solo destino, al lado de una casilla libre.

| Lugar | Qué es en el fondo | Casilla | Mira a | Roles (animación) |
|---|---|---|---|---|
| `door` | Delante de la puerta | 4,27 | abajo-der. | `entry` |
| `exit` | Salida: la esquina de adelante a la izquierda (la casilla del piso más a la izquierda, delante del mueble del equipo de música). Sin puerta dibujada: al abrir su programa aparecen ahí (mirando arriba-der.) y al cerrarlo caminan hasta ahí, se despiden y se desvanecen (`Character.outside`). `door` queda para las escenas de Flash | 16,30 | abajo-izq. | (abrir / cerrar el programa) |
| `couch` (grupo) | Sillón: `couch_left` 10,31, `couch_mid` 8,31, `couch_right` 6,31 (de Sheldon; Penny lo prefiere) | | abajo-der. | `rest` (`sit`), `read` (`read`) |
| `armchair` | Sillón individual beige, fuera del grupo `couch`: solo Leonard se sienta ahí (`only`: `leonard.couch = [armchair]`; nunca en el sillón grande; si estuviera ocupado va igual). Casilla de la huella del mueble (así no lo tapa), `offset` 12,16 (rodillas de Leonard en el borde del almohadón); se llega desde 5,33 | 4,33 | abajo-izq. (`sit`/`read` espejados) | `rest` (`sit`), `read` (`read`) de Leonard |
| `whiteboard` | Delante del pizarrón con atril (objeto agregado, en 1,38), entre el sillón individual y la isla | 2,38 | arriba-der. | `edit` (`write`), `think` (`think`) |
| `desk` (grupo) | Sillas detrás de los escritorios de adelante: `desk_left` 11,36 (de Leonard), `desk_right` 6,41 (de Sheldon) | | abajo-der. | `shell` (`type`) |
| `window` | Pasillo junto al escritorio con el telescopio, frente a la ventana | 2,29 | arriba-der. | `web` (`look`) |
| `kitchen` | Banqueta de adelante de la barra | 3,45 | abajo-der. | libre (comer) |
| `center` | Sobre la alfombra, delante de la mesa ratona | 10,35 | abajo-der. | `scene` |

Otros objetos del living que suman: biblioteca con cómics, sillón individual, mesa ratona, el árbol de moléculas, la heladera.

---|---|---|
| `door` | Puerta del departamento | `entry` |
| `couch` | El sillón (el lugar de Sheldon, en la punta) | `rest` (`sit`), `read` (`read`, con un cómic) |
| `whiteboard` | Pizarrón con ecuaciones | `edit` (`write`), `think` (`think`) |
| `desk` | Escritorio con las computadoras, junto a la ventana | `shell` (`type`) |
| `window` | Ventana con el telescopio | `web` (`look`) |
| `kitchen` | Cocina / mesada | libre (comida china en escenas) |
| `center` | Medio del living, sobre la alfombra | `scene` |

Otros objetos del living que suman al fondo: biblioteca con cómics, sillón individual, mesa ratona, mesa con cajas de comida china, el árbol de moléculas, la puerta del ascensor roto fuera de cuadro.

---

## 5. Animaciones

| Animación | Cuadros | FPS | Loop | Uso |
|---|---|---|---|---|
| `idle` | 4 | 4 | sí | Parado sin hacer nada |
| `walk` | 4 | 8 | sí | Caminar en 3/4 de frente (abajo-derecha; espejado, abajo-izquierda) |
| `walk_back` | 4 | 8 | sí | Caminar en 3/4 de espalda (arriba-derecha; espejado, arriba-izquierda) |
| `sit` | 4 | 4 | sí | Sentado en el sillón (reposo) |
| `type` | 4 | 8 | sí | Teclear en la compu (comandos) |
| `write` | 4 | 6 | sí | Escribir en el pizarrón (editar) |
| `think` | 4 | 4 | sí | Mano en el mentón frente al pizarrón |
| `read` | 4 | 4 | sí | Leer un cómic sentado |
| `look` | 4 | 4 | sí | Mirar por el telescopio (web) |
| `celebrate` | 4 | 8 | no | Turno largo sin errores |
| `argue` | 4 | 6 | sí | Discusión |
| `knock` | 3 | 6 | no | Golpear la puerta (antes de entrar) |
| `wave` | 10 | 6 | no | Saludar con la mano al entrar y en la puerta al irse (§6). Hoja de 4 cuadros con [PROMPT_SALUDO.md](PROMPT_SALUDO.md); el 1 viene de frente, así que va de ida y vuelta: Sheldon `--pick 1,2,3,4,3,4,3,4,2,1`, Penny y Leonard `--pick 1,2,3,2,3,2,3,2,3,1` (su cuadro 4 saluda con la otra mano) |
| `wii` | 16 | 6 | sí | Sheldon juega al bowling de la Wii, de frente, en `tv` (casilla 10,40 detrás de la tele, que le tapa las piernas). Hoja de 2×8 unida en una fila (`source/wii_row.png`) |
| `blanket_on` | 4 | 4 | no | Sheldon sentado en el sillón se pone la manta como capucha y saca la notebook roja del piso (§6) |
| `blanket_type` | 4 | 6 | sí | Teclea encapuchado con la notebook en las piernas; loop sin fin, dura lo que haga falta |
| `blanket_off` | 4 | 4 | no | Cierra la notebook, la deja en el piso y se saca la manta (termina en la pose de `sit`) |

---

## 6. Interacciones

| Disparador | Escena |
|---|---|
| Dos agentes tocan el mismo archivo | Disputa por el lugar en el sillón: "ese es mi lugar" (`argue` + globo); el que pierde se va a la silla |
| Un agente entra | `knock` tres veces con globo "knock knock knock" antes de entrar (solo Sheldon, o todos con probabilidad baja) |
| Error del proveedor (429 / 5xx) | El otro se ríe con globo "Bazinga!"; el afectado se enoja |
| Cambio a proveedor de respaldo | Sale y vuelve a entrar con otra remera |
| Turno largo sin errores | `celebrate`; si hay otro, festejan juntos |
| Dos agentes activos mucho rato | Discusión en el pizarrón con globos de ecuaciones |

Sin peleas físicas: todo pasa por discusiones y globos.

### Charlas (globos)

Todas en `wallpaper/public/js/sim/chatter.js` (frases y lógica) y `config.json` → `chatter` (frecuencias). La idea: que no haya silencios incómodos, cada uno habla como en la serie. En una prueba de 15 min con las tres IAs salió un globo cada ~8 s.

| Cuándo | Lista | Ejemplo |
|---|---|---|
| Llega al lugar de su tarea (`think`, `edit`, `shell`, `read`, `web`), y cada ~30 s si sigue ahí | `WORK[personaje][rol]` | Sheldon en la compu: «Si falla, es culpa del hardware.» · Leonard: «OmniRoute, no me falles ahora.» · Penny: «La clave era «Penny es linda».» |
| Sheldon con la manta (uso alto) | `BLANKET` | «Suave gatito... compilando...» |
| Entra (al terminar de aparecer, siempre): con alguien en el living saluda con la mano (`wave`) y **todos** los que están le contestan, de a uno; solo, un comentario sin saludar | `ENTER`, `GREET`, `ENTER_ALONE` | Penny: «Vengo a robar wifi. Hola.» → Leonard: «¡Penny! Hola. Hola... hola.» · solo, Leonard: «Silencio. Raro en esta casa.» |
| Se va por la salida (cerró su programa, siempre): camina a `exit` (esquina de adelante a la izquierda) y ahí, con alguien saluda con la mano y los que quedan lo despiden; solo, un comentario. Desaparece cuando se terminó de leer el globo | `LEAVE`, `BYE`, `LEAVE_ALONE` | Sheldon: «Hasta luego. ¡Bazinga!» → Penny: «Chau, Shelly.» |
| Se cruzan caminando en el mismo carril | `LINES` | «Cedé el paso: va la derecha.» → «Eso no es una ley, Sheldon.» |
| Choque: uno espera porque el otro le tapa la próxima casilla | `BUMP` | «Penny. Penny. Penny.» → «¡Ya me corro!» |
| Sentados en el living (sofá + sillón individual de Leonard): dos o tres, se hablan de a dos | `COUCH` | Penny: «¿Me masajeás los pies?» → Leonard (sillón): «¡Sí! Digo... si querés.» |
| Uno solo en el living, o Penny en la banqueta | `SOLO` | Leonard: «Mi sillón. El único sin cláusula.» |

Nadie arranca a hablar si otro tiene un globo a <= 4 casillas (`work.near`), así no se pisan con las disputas por el lugar ni con otras charlas, y no se repite la última frase de cada lista. Las frases tienen como mucho ~36 caracteres (globo de una línea). Para sumar personajes (Howard, Raj...) se agregan sus claves en cada lista.

### Escena especial: Sheldon es Flash

Cada tanto (Sheldon en reposo un rato largo, con probabilidad baja y enfriamiento largo, por ejemplo una vez cada 30–60 min):

1. Camina hasta la puerta de arriba a la izquierda (`door`) y desaparece unos segundos.
2. Vuelve a aparecer en la puerta con el traje de Flash (personaje aparte: `characters/sheldon_flash/`).
3. `flash_pose` un par de segundos: la pose de la figura (rodillas flexionadas, un puño adelante, la otra mano arriba).
4. Corre muy rápido (~4 veces la velocidad normal) por varias casillas al azar del living con `flash_run` / `flash_run_back`. Las **sombras atrás** se hacen por código: copias del sprite en las posiciones anteriores, cada vez más transparentes y teñidas de rojo/amarillo, más algún destello de rayo.
5. Se frena en algún lugar: `flash_pose` o `flash_idle` (parado normal con el traje).
6. Vuelve corriendo a la puerta, desaparece y reaparece como Sheldon normal, que camina de vuelta a donde estaba.

Hojas: referencia de 4 vistas de Sheldon con el traje (base para todas las demás), `flash_run`, `flash_run_back`, `flash_pose`, `flash_idle`.
Hechas: referencia (`extract_sheet.py --height 110`, Gemini lo dibujó más chico), `flash_pose`, `flash_run` (`--pick 2,3,2,3`: los otros cuadros estaban de frente y de perfil) y `flash_run_back`. Falta `flash_idle` (por ahora la vista quieta).
La estela: `walk_preview.with_trail`, clones de los últimos 6 cuadros, difuminados, teñidos hacia rojo/amarillo y cada vez más transparentes. La escena entera se probó con `flash_preview.py` → `flash_sheldon.mp4` (borrados en la limpieza; en vivo está en `wallpaper/public/js/sim/scenes.js`).

### Escena: Sheldon con la manta y la notebook

Sheldon en su lugar del sillón, encapuchado con la manta gris tejida y tecleando en la notebook roja. Tres animaciones encadenadas, sin caminar (se anima en el asiento, con el `offset` de `couch_*` igual que `sit`):

1. `blanket_on` (una vez): manta doblada en el regazo → la levanta → se la pone de capucha → saca la notebook del piso.
2. `blanket_type` (loop): teclea con el resplandor de la pantalla en la cara. **Se repite el tiempo que haga falta**: no tiene final propio, el guion decide cuándo cortar.
3. `blanket_off` (una vez): cierra la notebook → la deja en el piso → se saca la capucha → manta doblada en el regazo; sigue `sit`.

**Lógica: la IA en uso alto = esfuerzo alto de Claude.** El selector de esfuerzo de Claude Code (Bajo, Medio, Alto, Extra, Máx) se guarda por turno en el transcript (`perTurnEffort` de cada respuesta: `low`, `medium`, `high`, `xhigh`, `max`). El hook (`wallpaper/hooks/cc_hook.py`) lo lee del final del transcript (los últimos 256 KB, ~0,2 ms) y lo manda como `effort` en `request_start`, `tool_call` y `turn_end`; solo esa palabra, nada del contenido. En `request_start` todavía es el del turno anterior; se corrige en la primera herramienta.
- **Alto, Extra o Máx** (`config.json` → `scenes.blanket.high`): durante el turno Sheldon **no va al escritorio ni al pizarrón**; trabaja en su lugar del sillón (`wantRole()` = `rest` mientras `highEffort()`). Al llegar se pone la manta y teclea **sin límite de tiempo**: `startBlanket(hold)` con `hold()` = sigue en alto y trabajando; los eventos de herramientas no lo cortan. Cuando termina el turno (`turn_end` → `rest`) o el turno siguiente viene con menos esfuerzo, `hold()` da false: `blanket_off` y sigue normal (sentado en reposo, o va al lugar de su rol).
- **Bajo o Medio**: como siempre (escritorio, pizarrón...).
- Si se cierra la sesión con la manta puesta, se la saca y se va por la puerta (`leaveAfterScript`; también vale para la Wii y los demás guiones, que antes se quedaban hasta el `leave_after`).
- Para que Medio también cuente como alto: agregar `"medium"` a `scenes.blanket.high`.

**Además, en reposo (prueba):** está en el repertorio como la Wii (`config.json` → `scenes.blanket`): sentado en el sillón más de 60 s, 20 % cada 10 s, enfriamiento de 10 min, teclea un rato corto (15–45 s) o largo (2–6 min), mitad y mitad (`type`: lista de rangos). Siempre se saca la manta antes de levantarse: un evento lo corta con `blanket_off` (`blanketOff`, si todavía tenía la manta) y se va a su rol. Tecla **M** en la demo.

Hoja: `characters/sheldon/source/blanket.webp`, 3×4 sobre magenta (fila 1 `blanket_on`, fila 2 `blanket_type`, fila 3 `blanket_off`), a 2 px por píxel. Se extrae con `python -I "Assets BBTheory/blanket_sheet.py"` y no con `extract_anim.py`: la notebook en el piso queda debajo de los zapatos y la manta cuelga hasta el piso, así que el ancla sale de las canillas (los dos tonos claros del pantalón), calibrada contra `sit` para que el paso `sit` → `blanket_on` no salte. En `blanket_on` 2 la manta tapa las piernas: usa la mediana de la fila dentro de su celda. La notebook puede quedar por debajo del ancla.

### Escena especial: Leonard es Frodo

El disfraz de hobbit de Halloween (*The Middle-Earth Paradigm*). Mismas condiciones que la de Sheldon (en reposo un rato largo, probabilidad baja, enfriamiento largo), y nunca las dos a la vez.

1. Camina hasta el **pasillo a los cuartos** (`hallway`, casilla -5,34 mirando arriba-derecha): la franja de piso bajo la ventana de la derecha, en el rincón contra la heladerita verde. Son 6 casillas nuevas en `mark_grid.py` (el borde del piso ahora sigue la base de esa pared) y la heladerita es una capa más (`cut_layers.py minifridge`), así lo tapa al entrar. Desaparece unos segundos (tramado).
2. Vuelve a aparecer en el pasillo vestido de Frodo (personaje aparte: `characters/leonard_hobbit/`): capa élfica gris verdosa con broche de hoja, chaleco, camisa blanca, pantalón corto marrón, **pies descalzos peludos**, el Anillo colgando de una cadena.
3. Camina (con `walk` / `walk_back` de hobbit) hasta una casilla libre al azar.
4. `ring_on`: saca el Anillo de la cadena y se lo pone. En el último cuadro, destello dorado.
5. **Desaparece por código**: se disuelve con tramado (dither) en ~0,5 s, con unas chispas doradas, y la escena se oscurece apenas y se tiñe de gris (el "mundo de las sombras") mientras está invisible.
6. Reaparece en otra casilla libre al azar (lejos de la anterior), con el tramado al revés, todavía con el Anillo puesto, y se lo saca (`ring_on` al revés). Se puede repetir 1 o 2 veces: aparece en el sillón, al lado de la heladera...
7. Vuelve caminando al pasillo, desaparece y reaparece como Leonard normal, que vuelve a donde estaba.

Hojas: referencia de 4 vistas de Leonard hobbit (base para las demás), `walk`, `walk_back`, `idle` y `ring_on` (prompts en `characters/leonard/PROMPTS.md`). `ring_off` sale de `ring_on` al revés, y la desaparición, las chispas y el tinte son por código.
En el wallpaper: `frodo` / `frodoHome` en `wallpaper/public/js/sim/scenes.js` (tecla **H** en la demo).
La escena entera se probó con `frodo_preview.py` → `frodo_leonard.mp4` (~53 s, de noche con efectos; borrados en la limpieza, en vivo está en `wallpaper/public/js/sim/scenes.js`). Por código: tramado Bayer 4×4 fijo a la pantalla (10 cuadros, 0,5 s), chispas doradas de 2 px que suben y titilan, destello en cruz donde está el píxel dorado del Anillo en el último cuadro de `ring_on`, y el "mundo de las sombras" (escena 70 % gris y 18 % más oscura, entra y sale con la disolución). Las casillas al azar son lejanas (`MIN_JUMP` 9) y visibles: nunca una donde algún mueble lo taparía.

---

## 7. Efectos por código

- Resplandor de la tele parpadeando de noche.
- Ecuaciones que se van escribiendo en el pizarrón mientras alguien está en `edit`.
- Luces de la ciudad por la ventana de noche; nubes de día.
- Vapor saliendo de las cajas de comida china.
- Pantallas de las compus prendidas cuando alguien está en `shell`.

Hechos en `Assets BBad/tools/effects.py` (genérico: lee `theme.json` → `scene.effects`, todo en píxeles de `aligned/`). Bloques de `px: 2`, bandas duras con tramado y paleta corta; nada de degradés. Cada efecto dice en qué fondos va (`backgrounds`), si depende de un rol/lugar (`role`, `place`) y si va debajo de las capas y los personajes (`under`, se pinta también sobre los muebles recortados para que no lo borre la capa) o encima (`over`).
- **Tele** (`tv_glow`, tipo `glow`): la de en medio de los escritorios de adelante, que mira al sillón (se le ve el dorso). De noche (los dos fondos), un halo isométrico en 3 bandas tramadas sobre el piso y la alfombra hacia el sillón, detrás del mueble (`behind`), más un filo de luz arriba del aparato. Intensidad a saltos cada 0,12–0,6 s y color que cambia por "escena" cada ~1,8 s. De día no va.
- **Pizarrón** (`whiteboard`, tipo `board`): con alguien en `edit`, la tinta del dibujo del pizarrón (`props/whiteboard.png`) se borra y se vuelve a escribir por renglones paralelos al borde del pizarrón (a saltos, con la punta del marcador), 8 s escribiendo, 2 s quieto, se borra en 0,8 s de izquierda a derecha y vuelve a empezar. Sin nadie en `edit` queda el dibujo original. `polygon` es la superficie en coordenadas del prop.
- **Ventanas**: de día (`clouds`) nubes de bloques de 3 px que cruzan las dos ventanas solo sobre los píxeles de cielo (los marcos y edificios quedan adelante); de noche (`city_lights`) las luces y estrellas del fondo titilan (se apagan casi del todo a ratos) y se prenden y apagan ventanitas extra sobre los edificios. `rects` = vidrio de cada ventana.
- **Comida china** (`takeout`, tipo `sprite`, y `steam`): las cajas no estaban en el fondo, así que se dibujan por código (dibujito de 7×8 bloques en el json, con la luz de cada fondo) en la mesa ratona y la isla de la cocina; el vapor sale de cada caja y del bowl de la mesa ratona, va encima de todo y sube en bloques que se van desvaneciendo en 3 pasos.
- **Pantallas** (`screen_left` / `screen_right`, `spill_left` / `spill_right`): con alguien en `shell` en `desk_left`, la notebook (que se ve de frente) pasa a fondo azul oscuro con renglones de código que suben y un cursor; en `desk_right` el monitor se ve de espaldas, así que se prende un filo de luz arriba. En los dos, un reflejo azulado en 2 bandas sobre quien está sentado (`over`). Parpadeo de brillo chiquito.

Integración: `compose_scene.py ... --effects [--time 3]` (el rol sale de `sheldon@shell` o de la animación, `sheldon@desk:type`) y `walk_preview.py ... --effects` (los efectos de rol arrancan al llegar). Se probaron con `effects_preview.py` → `effects_day.mp4` y `effects_night.mp4` (borrados en la limpieza); hoy la comparación es `?ref=` del wallpaper contra `wallpaper/public/bundle/big_bang/_ref/`.

---

## 8. Pendiente

- [x] Decidir isométrico o corte lateral: isométrico, lógica tipo Habbo.
- [x] Adaptar `compose_scene.py` a grilla de casillas.
- [x] Fondos de día, noche sin agentes y noche con agentes.
- [x] Alinear (más de 500 puntos en común por fondo; la noche sin agentes venía 6 % más chica y con marco).
- [x] Marcar la grilla de casillas (siguiendo las baldosas del piso) y los `places`.
- [x] Capa de primer plano (muebles recortados) para poder pasar por detrás.
- [x] Hojas de referencia de Sheldon, Leonard y Penny (4 vistas, magenta), extraídas.
- [x] Probar escala sobre el fondo: ×1.
- [ ] Animaciones de la tabla de arriba. Hechas: Sheldon `walk` (con las piernas de la de Leonard, recoloreadas a su pantalón y zapatos: `walk_from_leonard.py`, mismo ciclo de 4 cuadros; la de 8 cuadros, hecha con `walk_legs.py` (borrado), quedó en `source/walk_8f.png`), `walk_back` (la hoja traía la misma zancada en los 4 cuadros y parecía deslizarse: `walk_cycle.py` arma zancada → paso → zancada → paso moviendo la pierna de atrás; el original queda en `anims/walk_orig.png`), `idle`, `sit`, `type`, `write`, `think` y `read`, todos sus roles (prueba: `Assets BBad/tools/walk_preview.py Sheldon door couch --theme big_bang` → `walk_sheldon.gif`; con `--anim type` / `--anim write` termina trabajando). `type` tiene `lower: 18` en `animations`: se dibuja más abajo para que el teclado apoye en el escritorio. `type` se rehizo de frente (hoja nueva, `--pick 1,2,3,2`: el cuadro 4 tiene otra cara); `animations.type.shift_by_character` la corre 10 px a la izquierda (Sheldon y Leonard) para centrarla en la silla, `--shift N` en `extract_anim.py`. Penny ya cae centrada.
  - Leonard (hojas en `characters/leonard/source/`, el `pick` queda en cada `anims/*.json`): `walk` (`--pick 2,3,2,3`: el 1 está de frente y el 4 de perfil), `walk_back`, `idle` (`--pick 2,2,3,2`), `think` (`--pick 2,3,4,3`), `sit`, `read`, `type` y, provisorias, `write` (`--pick 4,4,4,4`: es el único cuadro de espaldas, queda quieto) y `look` (`--pick 2,3,2,3`, de 3/4 de frente aunque `window` mira arriba-derecha). Atlas generado. `type` (rehecha de frente, `--pick 1,2,3,2`; la hoja vino a otra resolución y `extract_anim.py` forzó la celda de la referencia, el resultado se ve bien) usa `lower: 24` (antes 10; de frente y sin teclado flotaba sobre el escritorio) (`animations.type.lower_by_character`, o `--lower N` en `extract_anim.py`): su teclado está más abajo en la hoja que el de Sheldon. La hoja de referencia tenía el contorno teñido de magenta: se limpió (sheet y 4 vistas) y `extract_anim.py` ya no usa colores magenta de la referencia como destino. Se probó con `walk_leonard_*.mp4` y `test_*_leonard.png` (borrados en la limpieza). Regenerar: `write` (4 cuadros de 3/4 de espalda escribiendo, como la de Sheldon), `look` (de espalda mirando por el telescopio) y, si se quiere un paso completo, `walk` (4 cuadros de 3/4).
  - Penny (hojas en `characters/penny/source/`, prompts en `characters/penny/PROMPTS.md`): `walk`, `walk_back`, `idle` (`--pick 2,2,2,2`, provisoria: es el único cuadro de 3/4, el que se acomoda el pelo; los otros estaban de frente, espalda y perfil), `think` (`--pick 2,3,4,3`), `sit` (con copa de vino), `read` (revista), `type` (con el celular en vez del teclado; queda bien en la silla, el escritorio tapa las piernas), `argue`, `celebrate` (`--keep-y`, para el salto), `knock` y `write` (de espalda pero con el celular en vez del marcador; de lejos frente al pizarrón se lee bien). Atlas generado. Falta `look` (de espalda, mirando por el telescopio). `idle` queda así (decidido).
  - Leonard hobbit: referencia (`extract_sheet.py --order front,three_quarter,back,side --height 110`: la grilla salía en 4,2 y quedaba gigante; mide 104, un poco más bajo que Leonard), `idle` (`--pick 2,2,3,2`) `walk_back` (`--pick 1,2,3,2`), `walk` y `ring_on` (4 cuadros, sin loop, en `theme.json` → `animations`): todas sus hojas listas, atlas generado. Escena completa en `wallpaper/public/js/sim/scenes.js` (§6).
- [x] Efectos por código (§7): tele, pizarrón, ventanas (nubes / luces), vapor de la comida china y pantallas, en `effects.py` + `scene.effects`; opcionales con `--effects` en `compose_scene.py` y `walk_preview.py`.
- [ ] Al tener fondos: `config.json` → `"theme": "big_bang"`.
- [ ] Wallpaper en vivo: plan en [WALLPAPER.md](../WALLPAPER.md).
