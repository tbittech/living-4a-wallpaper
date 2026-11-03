# Saul: prompts para Gemini

Adjuntar en cada prompt:
1. La hoja de referencia de Saul (`source/saul.jpg`).
2. La hoja de la misma animación de otro personaje, para pose y encuadre: la de Sheldon (`Assets BBTheory/characters/Sheldon/source/<anim>.*`) o la de Penny si Sheldon no la tiene. Son de otro estilo (más altos): solo copiar la pose.

Guardar en `source/<anim>.jpg` y extraer con
`python -I "Assets BBad/tools/extract_anim.py" "Assets BBad/themes/breaking_bad/characters/saul/source/<anim>.jpg" saul <anim> --theme breaking_bad`
(`--pick` si Gemini mezcla vistas).

Animaciones del tema (`theme.json` → `roles`): `idle`, `walk`, `walk_back`, `wave`, `cook` (shell: habla por teléfono, no cocina), `write` (edit, de espaldas), `read`, `look` (web, de espaldas), `think`.

---

## Base (va al principio de todos)

```
Pixel art sprite sheet, 4 frames in a single horizontal row, evenly spaced.
Same character in every frame, matching the first attached reference sheet exactly:
Saul, chibi proportions (big head, small body), thinning brown hair combed back with a receding
hairline, big confident grin, light grey-blue shiny suit, light blue shirt, wide red and gold patterned tie,
dark brown shoes, gold watch,
1-pixel dark outline, short palette, 2-3 shade levels, same pixel size as the reference.
The second attached sheet only shows the pose for this animation (another character, different
proportions): copy the pose and the action, NOT its proportions or style.
Solid flat magenta background (#FF00FF), no shadows, no text, no borders, no ground line,
feet aligned on the same baseline in every frame.
```

## Por animación (agregar después de la base)

**walk**
```
3/4 view facing down-right in ALL 4 frames (no front view, no side view), walking cycle:
frame 1 left foot forward, frame 2 passing, frame 3 right foot forward, frame 4 passing.
Arms swing opposite to the legs, the tie swings slightly.
```

**walk_back**
```
3/4 back view in ALL 4 frames, walking away toward up-right (we see the back of his thinning hair and the grey suit). Walking cycle: left foot forward, passing, right foot forward, passing.
```

**idle**
```
3/4 view facing down-right, standing still with arms at his sides, subtle breathing loop
(shoulders rise 1 pixel in frames 2-3), in frame 4 he straightens his tie.
```

**wave**
```
3/4 view facing down-right, standing, raising his right hand to wave: frame 1 hand at waist,
frame 2 hand at shoulder, frame 3 hand above head palm open, frame 4 hand tilted (waving).
```

**cook**
```
3/4 view facing down-right, standing, talking on a big old cell phone held to his ear with one hand, the other hand gesturing
(open palm, pointing, counting on fingers, open palm). Persuasive, grinning.
```

**write**
```
3/4 back view (facing up-right, we see the back of his thinning hair and the grey suit), standing,
writing on a notebook on a table that is NOT drawn: right arm moves in front of him at waist
height, alternating position each frame; head slightly bowed.
```

**read**
```
3/4 view facing down-right, standing, holding an open legal folder with both hands at chest height,
reading; in frame 3 he turns a page, frame 4 back to reading.
```

**look**
```
3/4 back view (facing up-right), standing still looking out of a window that is NOT drawn,
hands clasped behind his back, head turns slightly left and right between frames.
```

**think**
```
3/4 view facing down-right, standing, one hand on the chin tapping his lips with a finger, the other arm
crossed under it, frame 3 raises a finger as if having an idea, frame 4 back to thinking.
```
