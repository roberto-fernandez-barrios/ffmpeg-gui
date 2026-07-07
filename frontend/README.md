# FFmpeg GUI — Frontend (Electron + React)

Interfaz de escritorio alternativa para el backend de `ffmpeg-gui`, construida con Electron, React, TypeScript, Vite y Tailwind CSS.

## Cómo se conecta con el backend

Esta aplicación no reimplementa la lógica de FFmpeg: llama al backend Python que vive en `../logic/`.

- `../logic/ffmpeg_logic.py` construye los comandos de FFmpeg (sin dependencias de PyQt, reutilizado también por la GUI de escritorio en `../gui/`).
- `../logic/cli.py` es un puente headless: lee una petición JSON por `stdin`, ejecuta el comando FFmpeg correspondiente y va emitiendo progreso/resultado como líneas JSON por `stdout`. No depende de PyQt.
- El proceso principal de Electron (`electron/main.ts`) hace `spawn` de `python logic/cli.py` por cada operación, reenvía el progreso al renderer por IPC (`operation:message`) y expone selectores de archivo/carpeta nativos.
- El renderer (`src/`) usa `window.api` (definido en `electron/preload.ts`) para lanzar operaciones, escuchar progreso y cancelar tareas — ver `src/hooks/useTaskQueue.ts`.

Requiere tener `python` y `ffmpeg`/`ffprobe` accesibles en el `PATH` del sistema (no se empaqueta un intérprete propio).

## Desarrollo

```bash
npm install
npm run dev
```

## Compilación

```bash
npm run build
```

Genera `dist/` (renderer) y `dist-electron/` (main/preload), y empaqueta el instalador con `electron-builder` según `electron-builder.json5`.
