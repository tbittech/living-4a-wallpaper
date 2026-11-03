# Jesse: prompts para Gemini

Adjuntar en cada prompt:
1. La hoja de referencia de Jesse (`source/jessejoy.jpg`).
2. La hoja de la misma animación de otro personaje, para pose y encuadre: la de Sheldon (`Assets BBTheory/characters/Sheldon/source/<anim>.*`) o la de Penny si Sheldon no la tiene. Son de otro estilo (más altos): solo copiar la pose.

Guardar en `source/<anim>.jpg` y extraer con
`python -I "Assets BBad/tools/extract_anim.py" "Assets BBad/themes/breaking_bad/characters/jesse/source/<anim>.jpg" jesse <anim> --theme breaking_bad`
(`--pick` si Gemini mezcla vistas).

Animaciones del tema (`theme.json` → `roles`): `idle`, `walk`, `walk_back`, `wave`, `cook` (shell), `write` (edit, de espaldas), `read`, `look` (web, de espaldas), `think`.

---

## Base (va al principio de todos)

```
Pixel art sprite sheet, 4 frames in a single horizontal row, evenly spaced.
Same character in every frame, matching the first attached reference sheet exactly:
Jesse, chibi proportions (big head, small body), black knit beanie, scruffy light brown stubble,
sleepy half-closed eyes, red hoodie over a black t-shirt, baggy blue jeans, white-soled sneakers,
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
Arms swing opposite to the legs, the hoodie strings bounce.
```

**walk_back**
```
3/4 back view in ALL 4 frames, walking away toward up-right (we see the black beanie and red hoodie). Walking cycle: left foot forward, passing, right foot forward, passing.
```

**idle**
```
3/4 view facing down-right, standing still with arms at his sides, subtle breathing loop
(shoulders rise 1 pixel in frames 2-3), in frame 4 he scratches the back of his neck.
```

**wave**
```
3/4 view facing down-right, standing, raising his right hand to wave: frame 1 hand at waist,
frame 2 hand at shoulder, frame 3 hand above head palm open, frame 4 hand tilted (waving).
```

**cook**
```
3/4 view facing down-right, standing, working at a lab table that is NOT drawn: both hands
in front at chest height holding a small glass flask, frame 1 holding it, frame 2 tilting it to pour,
frame 3 swirling it, frame 4 looking at it closely. Concentrating, tongue out.
```

**write**
```
3/4 back view (facing up-right, we see the black beanie and red hoodie), standing,
writing on a notebook on a table that is NOT drawn: right arm moves in front of him at waist
height, alternating position each frame; head slightly bowed.
```

**read**
```
3/4 view facing down-right, standing, holding an open book with both hands at chest height,
reading; in frame 3 he turns a page, frame 4 back to reading.
```

**look**
```
3/4 back view (facing up-right), standing still looking out of a window that is NOT drawn,
hands clasped behind his back, head turns slightly left and right between frames.
```

**think**
```
3/4 view facing down-right, standing, one hand on the chin scratching his stubble, the other arm
crossed under it, frame 3 raises a finger as if having an idea, frame 4 back to thinking.
```
