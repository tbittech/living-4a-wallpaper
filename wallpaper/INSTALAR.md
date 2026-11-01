# Instalar Living 4A en otra PC

1. Copiar la carpeta `wallpaper` a cualquier lado (cualquier disco o ruta, puede tener espacios).
2. Doble clic en **`install.bat`**.
3. Abrir (o reiniciar) Claude Code.

El instalador hace todo y se puede correr de nuevo sin problema (por ejemplo después de mover la carpeta: actualiza las rutas):

- **Python**: si no está, ofrece instalarlo con winget. Instala `aiohttp` para el servidor.
- **Hooks de Claude Code**: los agrega a `%USERPROFILE%\.claude\settings.json` apuntando a esta carpeta. Los demás hooks y ajustes quedan como estaban; deja una copia en `settings.json.bak-wallpaper`.
- **Lively Wallpaper**: si no está, ofrece instalarlo. Crea la entrada "Living 4A" y la pone de fondo.
- **Inicio de Windows**: el servidor arranca solo al iniciar sesión, y lo arranca en el momento.

Para sacarlo: doble clic en **`uninstall.bat`**. Saca los hooks, el inicio automático y la entrada de Lively, y frena el servidor. No borra la carpeta ni desinstala Python o Lively.

## Qué necesita cada parte

| Para | Hace falta |
|---|---|
| Ver y usar el wallpaper | Solo la carpeta `wallpaper` (el bundle ya viene exportado en `public/`) |
| Volver a exportar el bundle (`export_bundle.py`) | También `Assets BBTheory` y `Assets BBad` al lado de `wallpaper`, más `pip install numpy pillow` |

Sin Lively, el living se ve igual en el navegador en `http://127.0.0.1:8765/` (con el servidor andando).
Codex y Gemini se detectan solos por sus procesos; las llamadas de OmniRoute se leen de `~/.omniroute/call_logs` si existe.

Prueba rápida de que todo anda: `node tools/sim_test.mjs` (simula 30 minutos, tiene que dar `"clashes":0`).
