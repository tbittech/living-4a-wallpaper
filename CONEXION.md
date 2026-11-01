# La Van — lógica de conexión

Cómo llegan los eventos de cada IA a la escena (el tema activo: la van, el departamento…). La parte visual está en [IDEA_Y_ANIMACION.md](IDEA_Y_ANIMACION.md).

> **Estado:** todavía no se revisó el código de **claude-office** ni el de **OmniRoute**.
> Lo que sigue es el diseño propuesto; los puntos marcados como ❓ se confirman al leer los dos repos.

---

## 1. Panorama

```
 Claude Code ──(hooks)───────────────────────────────┐
                                                     ▼
 Codex (Windows) ──┐                         ┌──────────────┐   WebSocket   ┌──────────────┐
                   ├──► [tap] ──► OmniRoute  │   servidor   │ ────────────► │  frontend    │
 Gemini CLI (WSL) ─┘      │                  │  (de claude- │               │  (escena)    │
                          └──(eventos)──────►│   office)    │               │  en Lively   │
                                             └──────────────┘               └──────────────┘
```

- **Claude Code** se conecta como en el proyecto original: sus hooks mandan eventos al servidor.
- **Codex y Gemini** no se integran uno por uno: se escucha el tráfico que ya pasa por **OmniRoute**.
- Todos los eventos se normalizan a un mismo formato con un campo `source`, y el frontend elige el personaje según ese campo.

---

## 2. Formato de evento normalizado

```json
{
  "source": "codex",              // claude | codex | gemini
  "session": "abc123",            // id de conversación si se puede inferir, si no el cliente
  "type": "tool_call",
  "tool": "shell",                // solo en tool_call / tool_result
  "files": ["src/app.ts"],        // opcional: rutas que aparecen en los argumentos
  "status": 200,                  // opcional: código HTTP (errores)
  "provider": "openai",           // opcional: proveedor real que usó el combo
  "effort": "high",               // opcional (Claude Code): esfuerzo del turno, low | medium | high | xhigh | max
  "ts": 1793462400000
}
```

| `type` | Significado | Animación (ver IDEA §5) |
|---|---|---|
| `gateway_up` / `gateway_down` | OmniRoute se prendió o se apagó | Codex y Gemini pueden o no estar |
| `request_start` | Salió una request al modelo | `THINKING` |
| `tool_call` | El modelo pidió una herramienta | `WORKING(tool)` |
| `tool_result` | Volvió el resultado de esa herramienta | Vuelve a `THINKING` |
| `turn_end` | Respuesta final, sin herramientas | `IDLE` / `CELEBRATE` |
| `error` | 4xx / 5xx del proveedor | Escena de error |
| `fallback` | El combo pasó a otro proveedor | Escena de cambio de ropa |

El evento lleva **solo metadatos**: nunca el texto de los prompts ni las respuestas.

---

## 3. Claude Code (hooks)

Se reutiliza lo que ya hace claude-office ❓. Hooks relevantes:

| Hook | Evento normalizado |
|---|---|
| `UserPromptSubmit` | `request_start` |
| `PreToolUse` | `tool_call` (nombre y rutas de los argumentos) |
| `PostToolUse` | `tool_result` |
| `Stop` | `turn_end` |
| `SessionStart` / `SessionEnd` | entrada y salida del personaje de Claude |

Solo hay que agregar `"source": "claude"` a lo que ya manda.

---

## 4. OmniRoute (Codex y Gemini)

### 4.1 Cómo enganchar los eventos

En orden de preferencia, según lo que ofrezca OmniRoute ❓:

| Opción | Cómo | Pros / contras |
|---|---|---|
| **A. Logs o base de datos propios** | Leer en vivo el log de requests de OmniRoute | No toca nada; depende de cuánto detalle guarde |
| **B. Webhook o hooks propios** | Que OmniRoute avise al servidor | Ideal si existe |
| **C. Proxy delante de OmniRoute** | Codex y Gemini apuntan al proxy, que reenvía todo a OmniRoute sin cambios y en paralelo lee las respuestas | Funciona siempre; agrega un salto local |

Si se usa **C**:
- Escucha solo en `127.0.0.1` (y en la interfaz de WSL si hace falta, ver §6).
- **No retiene el streaming**: pasa cada chunk apenas llega y lo analiza en paralelo. Si no, las CLIs se ponen lentas.
- Nunca guarda cuerpos de requests ni el header `Authorization`.
- Si el proxy se cae, se vuelve a apuntar las CLIs directo a OmniRoute y todo sigue andando, solo sin la escena.

### 4.2 Quién es quién

Para separar a Codex de Gemini dentro del tráfico, en orden de preferencia:
1. **API key distinta** para cada cliente en OmniRoute (lo más confiable).
2. **Combo o nombre de modelo distinto**.
3. Header `User-Agent` de cada CLI.

### 4.3 Qué se deduce de cada request y respuesta

Depende del formato de API que use cada cliente contra OmniRoute ❓:

| Formato | Pidió una herramienta | Resultado de la herramienta (request siguiente) | Fin de turno |
|---|---|---|---|
| OpenAI Responses (Codex) | item `function_call` / `custom_tool_call` / `local_shell_call` | item `function_call_output` | respuesta sin llamadas |
| OpenAI Chat Completions | `message.tool_calls[]` | mensaje con `role: "tool"` | `finish_reason: "stop"` |
| Gemini API | `parts[].functionCall` | `parts[].functionResponse` | respuesta sin `functionCall` |
| Anthropic Messages | bloque `tool_use` | bloque `tool_result` | `stop_reason: "end_turn"` |

- En streaming (SSE) el nombre de la herramienta llega al principio del bloque; con eso alcanza para animar sin esperar al final.
- Las **rutas de archivo** se sacan de los argumentos de la herramienta (campos tipo `path`, `file_path`, o el encabezado de un parche). Sirven para detectar si dos agentes tocan el mismo archivo y disparar la pelea.
- El **resultado** de una herramienta solo se ve en la request siguiente, así que `tool_result` llega con un pequeño retraso. Para la animación no importa.

### 4.4 Presencia

- El servidor chequea cada ~10 s si OmniRoute responde (puerto o endpoint de salud ❓) → `gateway_up` / `gateway_down`.
- Con OmniRoute apagado, los personajes de Codex y Gemini no pueden aparecer.
- Con OmniRoute prendido, cada personaje entra con su primera request y se va tras ~3 min sin actividad.

---

## 5. Servidor y frontend

- Se parte del servidor de claude-office ❓ y se le agrega:
  - un endpoint para recibir eventos del tap de OmniRoute (o se integra el tap en el mismo proceso),
  - el campo `source` en todo el flujo,
  - el chequeo de presencia de OmniRoute.
- El servidor manda los eventos al frontend por **WebSocket**.
- El frontend se **reconecta solo** con espera creciente si el socket se corta.
- Al reconectarse, el servidor manda un **estado inicial** (quién está presente y qué está haciendo) para que el fondo no arranque vacío.

---

## 6. Gemini en WSL

- Si Gemini ya llega a OmniRoute hoy, con las opciones A o B no hay nada que hacer.
- Con la opción C (proxy en Windows), Gemini dentro de WSL tiene que llegar al proxy:
  - **Recomendado:** red `mirrored` de WSL2 (`networkingMode=mirrored` en `%UserProfile%\.wslconfig`) → `localhost` funciona igual que en Windows.
  - Si no: usar la IP del host Windows desde WSL y abrir el puerto del proxy en el firewall solo para la red de WSL.

---

## 7. Arranque automático

- Servidor (y proxy, si se usa) como **tarea programada al iniciar sesión** en Windows.
- Lively Wallpaper apuntando a `http://localhost:<puerto>` del frontend.
- Orden de arranque indistinto: el frontend espera y se reconecta, y el proxy responde con error claro si OmniRoute todavía no levantó.

---

## 8. Plan por fases

1. **Leer los repos**: claude-office (cómo recibe y dibuja los eventos) y OmniRoute (logs, hooks, puertos, formato que usa cada cliente).
2. **Solo Claude, en el navegador**: claude-office funcionando con el escenario del tema y el personaje de Claude.
3. **Codex vía OmniRoute**: enganche (A/B/C) + identificación + personaje de Codex.
4. **Gemini vía OmniRoute**: tercer personaje + red de WSL si hace falta.
5. **Interacciones**: discusiones, peleas, errores, fallback.
6. **Fondo de pantalla**: Lively + arranque automático.

---

## 9. Preguntas abiertas

- [ ] Link del repo de claude-office (o clonarlo en `E:\ProyectosIA`).
- [ ] Dónde está OmniRoute y cómo corre (carpeta, Docker, npm…), y en qué puerto.
- [ ] ¿Codex y Gemini usan API keys o combos distintos en OmniRoute?
- [ ] ¿Qué formato de API usa cada uno contra OmniRoute (Responses, Chat Completions, Gemini)?
- [ ] ¿Gemini en WSL llega a OmniRoute por `localhost` o por IP?
- [ ] Tercer personaje para Gemini.
