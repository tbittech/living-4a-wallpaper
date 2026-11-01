# Penny: prompts para Gemini

Adjuntar en cada prompt:
1. La hoja de referencia de Penny (`source/penny.jpg`).
2. La hoja de la misma animación de Sheldon (`../Sheldon/source/<anim>.*`), para que copie pose, encuadre y tamaño. Para `write` y `look` usar la de Sheldon y no la de Leonard (las de Leonard quedaron provisorias: de frente en vez de espalda).

Guardar cada resultado en `source/<anim>.png` (o .webp/.jpg) y avisar; se extrae con
`python -I "Assets BBad/tools/extract_anim.py" "Assets BBTheory/characters/penny/source/<anim>.jpg" penny <anim> --theme big_bang`
(si Gemini mete un cuadro de frente o de perfil, `--pick 2,3,2,3` como con Leonard).

Ojo: la hoja de referencia de Penny trae las vistas en orden frente, 3/4, **perfil, espalda** (`meta.json` → `views`), no frente, 3/4, espalda, perfil como las otras.

Orden sugerido (lo que más usa Gemini CLI primero): `walk`, `walk_back`, `idle`, `type`, `think`, `write`, `sit`, `read`, `look`.

---

## Base (va al principio de todos)

```
Pixel art sprite sheet, 4 frames in a single horizontal row, evenly spaced.
Same character in every frame, matching the first attached reference exactly:
Penny, chibi proportions, long wavy golden-blonde hair past the shoulders,
light gray open cardigan over a pink v-neck top, short blue denim shorts,
bare legs, brown ankle boots, friendly smile,
1-pixel dark outline, short palette, 2-3 shade levels.
Match the pose, framing and size of the second attached sheet (another character
doing the same animation), but draw Penny.
Solid flat magenta background (#FF00FF), no shadows on the background, no text,
no borders, no ground line, feet aligned on the same baseline in every frame.
```

## Por animación (agregar después de la base)

**walk**
```
3/4 view facing down-right in ALL 4 frames (no front view, no side view), walking cycle:
frame 1 left foot forward, frame 2 passing, frame 3 right foot forward, frame 4 passing.
Arms swing opposite to the legs, hair bounces slightly.
```

**walk_back**
```
3/4 back view in ALL 4 frames, walking away toward up-right (we mostly see her long blonde
hair over the gray cardigan, a bit of her right cheek). Walking cycle: left foot forward,
passing, right foot forward, passing. Boot heels visible.
```

**idle**
```
3/4 view facing down-right, standing still, weight on one hip, subtle breathing loop;
in one frame she tucks a strand of hair behind her ear.
```

**type**
```
3/4 view facing down-right, sitting on an office chair (seen from the side, no desk drawn),
hands typing on a flat dark keyboard held at waist height in front of her,
fingers alternate between frames, head slightly forward looking at a screen, a bit bored.
```

**think**
```
3/4 view facing down-right, standing, one finger tapping her chin, other arm crossed
under it, small head tilt changes between frames, eyes looking up.
```

**write**
```
3/4 BACK view in ALL 4 frames: we see her back and long blonde hair, facing up-right toward
a whiteboard in front of her (do not draw the whiteboard), a bit of her right cheek visible.
One arm raised holding a marker, writing; the arm moves to a different spot each frame.
```

**sit**
```
3/4 view facing down-right, sitting relaxed on a couch (do not draw the couch),
legs crossed, one hand holding a glass of red wine, subtle breathing loop,
in one frame she takes a small sip.
```

**read**
```
3/4 view facing down-right, sitting (do not draw the seat), reading a colorful glossy
magazine held open with both hands, in one frame she turns a page.
```

**look**
```
3/4 BACK view in ALL 4 frames: facing up-right, away from the camera, standing and bending
slightly to look through the eyepiece of a big telescope on a tripod in front of her
(draw only the eyepiece end near her face), hand on the telescope, small adjustments between frames.
```

**celebrate** (no loop)
```
3/4 view facing down-right, celebrating: frame 1 fists pumped at chest, frame 2 small jump
with both arms up, frame 3 landing with arms up, frame 4 a wink with a thumbs up.
```

**argue**
```
3/4 view facing down-right, standing, arguing: hands on hips, then pointing a finger
forward, then arms crossed with an annoyed face, then pointing again. Hair moves with the head.
```

**knock** (3 cuadros: pedir "3 frames" en vez de 4 en la base)
```
3/4 BACK view facing up-right toward a door (do not draw the door), knocking with one fist:
frame 1 fist pulled back, frame 2 fist forward touching the door, frame 3 fist pulled back.
```

Checklist al recibir cada hoja: Penny en los 4 cuadros (pelo rubio largo, saquito gris, top rosa, short de jean, botitas marrones), 4 cuadros separados, fondo magenta parejo, sin texto, pies a la misma altura. Si Gemini la hace con la ropa de Cheesecake Factory que dice `BIG_BANG.md` §2, se puede pedir a propósito como variante; la referencia actual es ropa de calle.
