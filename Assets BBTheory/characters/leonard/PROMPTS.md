# Leonard: prompts para Gemini

Adjuntar en cada prompt:
1. La hoja de referencia de Leonard (`source/Gemini_Generated_Image_7viedn7viedn7vie.jpg`).
2. La hoja de la misma animación de Sheldon (`../sheldon/source/<anim>.*`), para que copie pose, encuadre y tamaño.

Guardar cada resultado en `source/<anim>.png` (o .webp/.jpg) y avisar; se extrae con
`python -I "Assets BBad/tools/extract_anim.py" "Assets BBTheory/characters/leonard/source/<anim>.png" leonard <anim> --theme big_bang`.

Orden sugerido (lo que más usa Codex primero): `walk`, `walk_back`, `idle`, `type`, `think`, `write`, `sit`, `read`, `look`.

---

## Base (va al principio de todos)

```
Pixel art sprite sheet, 4 frames in a single horizontal row, evenly spaced.
Same character in every frame, matching the first attached reference exactly:
Leonard, chibi proportions, curly dark brown hair, thick black square glasses,
olive green zip hoodie open over a navy t-shirt, blue jeans, brown shoes,
1-pixel dark outline, short palette, 2-3 shade levels.
Match the pose, framing and size of the second attached sheet (another character
doing the same animation), but draw Leonard.
Solid flat magenta background (#FF00FF), no shadows on the background, no text,
no borders, no ground line, feet aligned on the same baseline in every frame.
```

## Por animación (agregar después de la base)

**walk**
```
3/4 view facing down-right in ALL 4 frames (no front view, no side view), walking cycle:
frame 1 left foot forward, frame 2 passing, frame 3 right foot forward, frame 4 passing.
Arms swing opposite to the legs.
```

**walk_back**
```
3/4 back view, walking away toward up-right (we see his back and the hood, a bit of
the right side of his face and glasses). Walking cycle: left foot forward, passing,
right foot forward, passing.
```

**idle**
```
3/4 view facing down-right, standing still, subtle idle loop: slight breathing,
in one frame he pushes his glasses up the nose with one finger.
```

**type**
```
3/4 view facing down-right, sitting on an office chair (seen from the side, no desk drawn),
hands typing on a flat dark keyboard held at waist height in front of him,
fingers alternate between frames, head slightly forward looking at a screen.
```

**think**
```
3/4 view facing down-right, standing, hand on chin thinking, small head tilt changes
between frames, eyes looking up.
```

**write**
```
3/4 BACK view in ALL 4 frames: we see his back and the hood, facing up-right toward a
whiteboard in front of him (do not draw the whiteboard), a bit of his right cheek and glasses
visible. One arm raised holding a marker, writing; the arm moves to a different spot each frame.
```

**sit**
```
3/4 view facing down-right, sitting relaxed on a couch (do not draw the couch),
hands on his lap, subtle breathing loop.
```

**read**
```
3/4 view facing down-right, sitting (do not draw the seat), reading a comic book held
with both hands, in one frame he turns a page.
```

**look**
```
3/4 BACK view in ALL 4 frames: facing up-right, away from the camera, standing and bending
slightly to look through the eyepiece of a big telescope on a tripod in front of him
(draw only the eyepiece end near his face), hand on the telescope, small adjustments between frames.
```

Checklist al recibir cada hoja: Leonard en los 4 cuadros (anteojos, buzo verde abierto), 4 cuadros separados, fondo magenta parejo, sin texto, pies a la misma altura.

---

# Leonard hobbit (escena especial: Frodo)

Guardar en `Assets BBTheory/characters/leonard_hobbit/source/`. Primero la referencia; después, en cada animación, adjuntar la referencia hobbit ya hecha y la hoja de Leonard normal de la misma animación (`leonard/source/<anim>.jpg`).

**reference → `reference.jpg`** (adjuntar la referencia de Leonard normal y la foto del disfraz)
```
Pixel art character reference sheet. Same character as the first attached image (Leonard: chibi proportions, curly dark brown hair, thick black square glasses, same face, same height, same pixel style and outline), but wearing the Frodo hobbit costume from the second attached photo:
long dark forest-green cloak with hood down, fastened at the neck with a small silver-green leaf brooch; white loose long-sleeve shirt with rolled cuffs; brown suede waistcoat with a row of small buttons; dark reddish-brown velvet trousers, baggy, gathered just below the knee; big bare hairy hobbit feet, tan and furry, no shoes; a small short sword (Sting) in a scabbard at his left hip; a tiny gold ring on a thin chain around his neck. Keep the thick black glasses.
4 views in a single horizontal row, in this order: front, 3/4 view facing right, back 3/4 view (walking away to the upper right), side view facing right. Same height in every view.
1-pixel dark outline, short palette, 2-3 shade levels, no photo details or textures.
Solid flat magenta background (#FF00FF), no shadows, no text, no borders, feet aligned on the same baseline.
```

**Base de las animaciones** (va al principio de walk, walk_back, idle y ring_on)
```
Pixel art sprite sheet, 4 frames in a single horizontal row, evenly spaced.
Same character in every frame, matching the first attached reference exactly: Leonard dressed as Frodo the hobbit: curly dark brown hair, thick black square glasses, long dark green cloak with a leaf brooch, white shirt, brown suede buttoned waistcoat, baggy dark reddish-brown velvet trousers gathered below the knee, bare hairy hobbit feet, small sword in a scabbard at the hip, gold ring on a chain around his neck. Chibi proportions, 1-pixel dark outline, short palette.
Match the pose, framing and size of the second attached sheet (same character without the costume), but keep the hobbit costume.
Solid flat magenta background (#FF00FF), no shadows on the background, no text, no borders, no ground line, feet aligned on the same baseline in every frame.
```

**walk → `walk.jpg`**
```
Animation: 3/4 view facing down-right in ALL 4 frames (no front or side view), walking cycle: frame 1 left foot forward, frame 2 passing, frame 3 right foot forward, frame 4 passing. Arms swing opposite to the legs, the cloak sways a little behind him.
```

**walk_back → `walk_back.jpg`**
```
Animation: 3/4 back view walking away toward up-right (we mostly see the green cloak and his curly hair, a bit of the glasses on the right side). Walking cycle: left foot forward, passing, right foot forward, passing. Hairy bare heels visible.
```

**idle → `idle.jpg`**
```
Animation: 3/4 view facing down-right, standing still, subtle breathing; in one frame he touches the ring on his chain nervously with one hand.
```

**ring_on → `ring_on.jpg`** (adjuntar solo la referencia hobbit)
```
Animation: 3/4 view facing down-right, standing. Frame 1: he holds the gold ring on its chain, looking at it. Frame 2: ring in his open palm in front of his chest, chain pulled from his neck. Frame 3: slipping the ring onto his raised index finger, dramatic serious face. Frame 4: ring on the finger, hand raised, small golden glint on the ring.
```

Checklist: anteojos puestos, capa verde, chaleco marrón, pantalón bordó/marrón hasta abajo de la rodilla, pies descalzos peludos, misma altura que Leonard normal. Si Gemini lo hace muy realista o con texturas de foto, repetir la referencia adjuntando solo la hoja de Leonard normal y pegando la descripción del disfraz.
