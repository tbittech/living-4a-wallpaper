# Prompt universal: saludo (`wave`)

Sirve para cualquier personaje (Sheldon, Leonard, Penny, Howard, Raj, disfraces...). No hay que editar nada: el personaje sale de la imagen adjunta.

Adjuntar:
1. **La hoja de referencia del personaje** (la de 4 vistas sobre magenta, `characters/<nombre>/source/...`). Obligatoria.
2. *(Opcional, recomendado)* Una hoja ya hecha de otra animación del mismo personaje (por ejemplo `idle` o `walk`), para que respete tamaño y encuadre.

Guardar el resultado en `characters/<nombre>/source/wave.png` (o .webp/.jpg) y extraer con
`python -I "Assets BBad/tools/extract_anim.py" "Assets BBTheory/characters/<nombre>/source/wave.png" <nombre> wave --theme big_bang`
(si Gemini mete un cuadro de frente o de perfil, `--pick` como con las otras).

Reproducción sugerida: 4 cuadros, 6 FPS; se puede pasar 1 → 2 → 3 → 4 → 3 → 4 → 2 → 1 para un saludo de ida y vuelta.

---

```
Pixel art sprite sheet of a GREETING / WAVING animation: exactly 4 frames in a single
horizontal row, evenly spaced, same cell size for every frame.

CHARACTER: draw exactly the character shown in the FIRST attached image. Copy everything
from it: face, hairstyle and hair color, skin tone, glasses or accessories, every piece of
clothing with its colors and prints, shoes, body proportions and height. Do not redesign,
restyle, add or remove anything. If a SECOND image is attached, it is another animation of
the same character: match its scale, framing and pixel density exactly.

STYLE: chibi pixel art, large head (about one third of the total height), short body and
legs, crisp 1-pixel dark outline, short limited palette, 2-3 shade levels per color, hard
pixel edges, no anti-aliasing, no gradients, no blur. Tall narrow figure (roughly 1:3
width to height), the same size in all 4 frames.

VIEW: 3/4 view facing down-right toward the camera in ALL 4 frames. No front view, no side
view, no back view. The character looks at the viewer with a friendly smile.

ANIMATION (friendly hello wave, standing in place, feet do not move):
- Frame 1: standing relaxed, the waving arm (the one closest to the camera) starting to
  rise from the side, elbow bent, small smile.
- Frame 2: the hand raised next to the head, palm open facing the viewer, fingers spread,
  big smile, eyebrows up.
- Frame 3: same raised arm, the hand tilted outward (wave to one side), head tilted slightly
  the same way.
- Frame 4: same raised arm, the hand tilted inward (wave to the other side), head tilted
  slightly the other way, eyes closed happily or a wink.
The other arm stays relaxed at the side. Only the waving arm, the hand, the head tilt and
the facial expression change between frames; body, legs and clothing stay identical.
Hair and loose clothing may sway one pixel with the motion.

LAYOUT RULES: solid flat magenta background (#FF00FF) filling the whole image, no shadows
on the background, no ground line, no floor, no props, no text, no labels, no frame numbers,
no borders or grid lines. Generous empty magenta space between frames so no frame touches
another. Feet aligned on exactly the same baseline in every frame, and the character's body
at the same horizontal position inside each cell (only the arm moves).
```

---

Checklist al recibir la hoja: es el mismo personaje que la referencia (ropa, pelo, colores), 4 cuadros separados, los 4 en 3/4 mirando abajo-derecha, solo se mueve el brazo y la cabeza, pies a la misma altura, fondo magenta parejo, sin texto.

Si sale mal, agregar al final del prompt según el caso:
- Cambió la ropa o la cara: `The character must be identical to the first attached image, pixel style included.`
- Algún cuadro de frente/perfil: `Every frame must be the same 3/4 down-right view as frame 1.`
- Muy grande o muy chico respecto de otras hojas: `Same character height in pixels as the second attached image.`
