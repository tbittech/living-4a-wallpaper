# Instalar Living 4A en otra PC con una IA

Guía para que un agente (Claude Code, Codex, Gemini CLI...) instale el fondo animado en una PC con Windows.
Pasale este archivo a la IA y decile: «seguí INSTALAR_CON_IA.md». La guía para hacerlo a mano está en [wallpaper/INSTALAR.md](wallpaper/INSTALAR.md).

---

## Instrucciones para la IA

Trabajá en PowerShell. Mostrale al usuario qué vas a hacer antes de cada paso que instala algo (winget) o toca `~/.claude/settings.json`.

### 1. Requisitos
- Windows 10 u 11 con `winget`.
- `git`: si `git --version` falla, `winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements`.
- Python 3: si `python --version` falla (o abre la Tienda), `winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements`. Después abrí una terminal nueva o refrescá el PATH.
- Lively Wallpaper (el que pone la página como fondo): si no está, `winget install -e --id rocksdanister.LivelyWallpaper --accept-source-agreements --accept-package-agreements`. Abrilo una vez para que cree su carpeta.

Instalá Python y Lively **antes** de correr el instalador: si faltan, `install.ps1` pregunta con `Read-Host`, y eso falla en una terminal sin entrada.

### 2. Bajar el repo
Preguntale al usuario dónde lo quiere (por defecto `%USERPROFILE%\living-4a`). La ruta puede tener espacios.
```powershell
git clone https://github.com/tbittech/living-4a-wallpaper.git "$env:USERPROFILE\living-4a"
cd "$env:USERPROFILE\living-4a"
```
Los dos temas (Big Bang y Breaking Bad) vienen en `main`.

### 3. Elegir el tema
`wallpaper/public/config.json` → `"theme"`:

| Valor | Escenario | Claude / Codex / Gemini |
|---|---|---|
| `big_bang` | living de Big Bang Theory | Sheldon / Leonard / Penny |
| `breaking_bad` | la casa rodante en el desierto | Walter / Jesse / Saul |

Preguntale al usuario cuál quiere y cambiá solo ese valor (la línea `"theme": "big_bang",` del principio). No toques el resto del archivo.

### 4. Instalar
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "wallpaper\scripts\install.ps1"
```
Hace lo siguiente, y se puede volver a correr sin problema:
- instala `aiohttp`;
- agrega los hooks de Claude Code a `%USERPROFILE%\.claude\settings.json`, sin tocar los que ya había (deja una copia en `settings.json.bak-wallpaper`);
- crea el fondo «Living 4A» en Lively y lo pone;
- deja el servidor (`wallpaper/server/server.py`, solo en 127.0.0.1:8765) arrancando con Windows y lo arranca en el momento.

Opciones: `-NoLively` (sin Lively), `-NoStartup` (sin arranque con Windows).

### 5. Comprobar
- `Invoke-WebRequest http://127.0.0.1:8765/state -UseBasicParsing` tiene que contestar 200.
- Abrí `http://127.0.0.1:8765/?demo=1&sources=claude,codex,gemini` en el navegador: los tres personajes entran y trabajan solos (simulación).
- Contale al usuario que reinicie Claude Code para que tome los hooks. Al abrir Claude, su personaje entra al fondo. Codex y Gemini CLI se detectan solos por sus procesos.

### Si algo falla
- **Lively no muestra nada:** `powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\lively_mode.ps1 live`.
- **El puerto 8765 está ocupado:** otro servidor viejo sigue corriendo. Mirá `wallpaper/server/.running.json`.
- **Desinstalar:** `powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\uninstall.ps1`. Saca los hooks, el arranque y la entrada de Lively; no borra la carpeta.

Solo hace falta la carpeta `wallpaper/`: el bundle ya viene exportado. Para volver a exportarlo (`wallpaper/export_bundle.py`) hacen falta `Assets BBad/`, los assets del tema y `pip install numpy pillow`.
