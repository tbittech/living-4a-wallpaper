# Tema: Breaking Bad, la van

La casa rodante en el desierto, vista en corte lateral. Ya anda en el wallpaper (`?theme=breaking_bad`); faltan las animaciones de acción de Gemini.
Lo general (estados, roles, procesamiento) está en [IDEA_Y_ANIMACION.md](../../IDEA_Y_ANIMACION.md); cómo se arma un tema, en [NUEVO_WALLPAPER.md](../../NUEVO_WALLPAPER.md).

## Estado (2026-11-03)

| Qué | Estado |
|---|---|
| Fondos alineados | hechos, a la mitad: `aligned/` 1342×760 (`backgrounds.output_scale` 0.5) |
| Grilla, lugares, capa de la puerta | hechos (`mark_grid.py`) |
| Efectos del fondo | hechos (ver abajo) |
| Walter (Claude) | `walk`, `idle`, `cook`, `think`, `read`, `write` (`--pick 1,4,1,4`) de Gemini; `walk_back` por código. Faltan `look`, `wave` |
| Jesse (Codex) | `idle`, `walk`, `walk_back` por código. Faltan todas las de Gemini (el `idle` nuevo es prendiendo un pucho: prompt listo, pose de `think` de Sheldon) |
| Saul (Gemini) | hoja de referencia de Gemini (`source/saul.jpg`); `idle`, `walk`, `walk_back` por código. Faltan las de Gemini |
| Acciones que faltan | la tanda del 2026-11-03 dio 429 desde la 5.ª hoja (cupo de imágenes agotado en todas las cuentas). Mientras tanto usan `idle` o la vista quieta |
| Frases (`chatter.js`) | hechas: cruces, choques, trabajo, entrar/salir, charla en los lugares de reposo (`couch.group: "rest"`) |
| Escenas | `highFive` (`scenes.js`, `config.scenes.highfive`, tecla C): Jesse pregunta cuánto toca a cada uno, Walter se niega a chocar los cinco y al final choca. Usa `wave` para las manos (sin `wave`, quedan quietos) |

### Cómo seguir cuando vuelva la cuota
De a una (OmniRoute atiende una imagen por vez; en paralelo se cortan por tiempo):
```
python -I "Assets BBad/themes/breaking_bad/gen_anim.py" walter cook
python -I "Assets BBad/tools/extract_anim.py" "Assets BBad/themes/breaking_bad/characters/walter/source/cook.jpg" walter cook --theme breaking_bad
```
`gen_anim.py` arma el prompt con `characters/<p>/PROMPTS.md` (bloque Base + el de la animación) y pasa la hoja del personaje y la misma animación de Sheldon como referencia. Mirar la hoja antes de extraer; `--pick` si mezcla vistas.
Una hoja nueva de `idle`/`walk`/`walk_back` pisa la hecha por código; `code_anims.py` no pisa las que vienen de una hoja.
Después: `python -I wallpaper/export_bundle.py --theme breaking_bad`.

## Reparto

| IA | Personaje |
|---|---|
| Claude Code | Walter |
| Codex (vía OmniRoute) | Jesse |
| Gemini CLI | Saul (abogado; en `cook` habla por teléfono) |

## Escena

Van de costado: la grilla es rectangular (casillas de 17×8 px, a = profundidad, b = izquierda a derecha) con direcciones propias (`scene.facings`): moverse a los costados usa la vista 3/4 (espejada a la izquierda), alejarse la de espaldas.
Piso: franja angosta delante de la mesa (2 filas) y baldosas a la derecha (hasta 5 filas). Escala ×2 (`sprite_scale`; el exportador agranda los atlas).

| Lugar | Rol / uso |
|---|---|
| `door`, `exit` | umbral de la puerta de atrás; la pared de la derecha es capa (`door_wall`) |
| `lab_right`, `lab_left` (grupo `lab`) | `shell` → `cook` (Walter tiene `lab_right`) |
| `bench` | `edit` → `write`, de espaldas sobre la mesa |
| `barrels` | `read` |
| `window` | `web` → `look`, de espaldas a la ventana izquierda |
| `center` | `think`, `scene` |
| `rest_a/b/c` (grupo `rest`) | `rest` → `idle`, uno por personaje |

Lo propio del tema en el wallpaper (home, escenas, charla sin sillón) está en `wallpaper/public/config.json` → `themes.breaking_bad`.

## Efectos (`scene.effects`)

Nubes de día y de noche, estrellas que titilan (`lights` sobre el cielo), mechero que parpadea, lámpara del medio (noche con IAs), vapor de los frascos y burbujas, humo por el techo mientras alguien está en `shell`, y planta rodadora (`tumbleweed`, tipo nuevo) cada 75 s de día / 110 s de noche, con chance.

## Pendientes

- Animaciones de acción (arriba).
- Los manchones de luz rectangulares sobre la arena de `night_active` son de la imagen original: se pueden borrar y reemplazar por un resplandor por código.
- Interacciones de la idea original: pelea por el mismo archivo (`punch` → `hit` → `fall`), risa ante un error del proveedor, `celebrate`, traje amarillo para `cook`, sombrero de Heisenberg.
- Hojas que faltan, de a una cuando vuelva el cupo: walter look, wave; jesse walk, idle, cook, think, read, write, look, wave, walk_back; saul igual que Jesse. Primero `walter wave` y `jesse wave` (las usa el choque de cinco).
