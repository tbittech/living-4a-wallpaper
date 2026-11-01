# Living 4A: fondo de pantalla animado para tus IAs

Un living isométrico en pixel art, al estilo de Big Bang Theory, que sirve de fondo de pantalla animado (con [Lively Wallpaper](https://www.rocksdanister.com/lively/)). Cada asistente de IA que tenés abierto es un personaje:

| Programa | Personaje |
|---|---|
| Claude (app y Claude Code) | Sheldon |
| Codex | Leonard |
| Gemini CLI | Penny |

Cuando abrís el programa, el personaje entra al living. Según lo que esté haciendo la IA va a la compu, al pizarrón o al sillón (con los hooks de Claude Code, o con los logs de OmniRoute para Codex y Gemini). Al cerrar el programa se despide y se va. En reposo pasean, charlan en el sillón, Sheldon juega a la Wii, y cada tanto aparecen Sheldon Flash o Leonard Frodo. El fondo cambia de día a noche según la hora.

## Instalar (Windows)

1. Descargá el repo (botón **Code → Download ZIP**) y copiá la carpeta `wallpaper` a donde quieras.
2. Doble clic en `wallpaper/install.bat`.
3. Abrí (o reiniciá) Claude Code.

El instalador consigue Python y Lively si te faltan (con winget), agrega los hooks a `~/.claude/settings.json` sin tocar los que ya tenés (deja una copia de respaldo), crea el fondo en Lively y deja el servidor arrancando con Windows. Para sacarlo: `wallpaper/uninstall.bat`. Más detalle en [wallpaper/INSTALAR.md](wallpaper/INSTALAR.md).

Sin Lively también se puede ver en el navegador, en `http://127.0.0.1:8765/` (`?demo=1` simula a los tres personajes).

## Privacidad

El servidor escucha solo en `127.0.0.1`. Los hooks mandan el tipo de evento, el nombre de la herramienta, el id de la sesión y la hora: nunca prompts, código ni contenido de archivos. Ver `wallpaper/server/server.py`.

## Estructura

- `wallpaper/`: el fondo (frontend en JS plano, servidor aiohttp, hooks, instaladores). Es lo único que hace falta para usarlo.
- `Assets BBTheory/`: el tema (fondos, personajes, animaciones, `theme.json`) y sus scripts.
- `Assets BBad/tools/`: herramientas para armar temas (extraer sprites y animaciones de hojas, alinear fondos, grilla, capas, efectos). Para volver a exportar el bundle: `pip install numpy pillow` y `python wallpaper/export_bundle.py`.
- `WALLPAPER.md`, `ESTADO.md`, `BIG_BANG.md`: diseño y notas de desarrollo (en español).

## Licencia y copyright

- **Código**: MIT (ver [LICENSE](LICENSE)).
- **Arte**: fan art sin fines de lucro, fuera de la licencia MIT. Los sprites y fondos se hicieron para este proyecto (con ayuda de Gemini). Sheldon, Leonard, Penny y *The Big Bang Theory* son de sus dueños (Warner Bros. / Chuck Lorre Productions / CBS). Este proyecto no tiene relación con ellos. Usalo solo para uso personal; no lo vendas. Si sos titular de derechos y querés que se saque algo, abrí un issue.
- La distribución del living se inspiró en un fan art de otro artista, que no se incluye ni se copia.
