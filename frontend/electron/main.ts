import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { spawn, spawnSync, type ChildProcessWithoutNullStreams } from 'node:child_process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.mjs
// │
process.env.APP_ROOT = path.join(__dirname, '..')

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST

let win: BrowserWindow | null

// El backend Python (logic/cli.py) vive junto a ffmpeg_logic.py, un nivel por
// encima de esta carpeta de frontend.
const BACKEND_DIR = path.join(process.env.APP_ROOT, '..', 'logic')
const CLI_PATH = path.join(BACKEND_DIR, 'cli.py')

function resolvePythonExecutable(): string {
  const candidates = ['python', 'python3', 'py']
  for (const candidate of candidates) {
    const probe = spawnSync(candidate, ['--version'])
    if (!probe.error) {
      return candidate
    }
  }
  return 'python'
}

const PYTHON_EXECUTABLE = resolvePythonExecutable()

type OperationEntry = {
  child: ChildProcessWithoutNullStreams
  finished: boolean
}

const operations = new Map<string, OperationEntry>()

function sendOperationMessage(requestId: string, data: unknown) {
  win?.webContents.send('operation:message', { requestId, data })
}

function startOperation(operation: string, params: unknown): { requestId: string } {
  const requestId = randomUUID()
  const child = spawn(PYTHON_EXECUTABLE, ['-u', CLI_PATH], {
    cwd: BACKEND_DIR,
    windowsHide: true,
  })

  operations.set(requestId, { child, finished: false })

  child.stdin.write(JSON.stringify({ operation, params }) + '\n')

  let buffer = ''
  child.stdout.on('data', (chunk: Buffer) => {
    buffer += chunk.toString()
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      try {
        const data = JSON.parse(trimmed)
        if (data.type === 'result') {
          const entry = operations.get(requestId)
          if (entry) entry.finished = true
        }
        sendOperationMessage(requestId, data)
      } catch {
        // Ignora líneas que no sean JSON válido (p. ej. logs sueltos de ffmpeg).
      }
    }
  })

  let stderrOutput = ''
  child.stderr.on('data', (chunk: Buffer) => {
    stderrOutput += chunk.toString()
  })

  child.on('close', () => {
    const entry = operations.get(requestId)
    if (entry && !entry.finished) {
      sendOperationMessage(requestId, {
        type: 'result',
        success: false,
        error: stderrOutput.trim() || 'El proceso de backend finalizó de forma inesperada.',
      })
    }
    operations.delete(requestId)
  })

  return { requestId }
}

function cancelOperation(requestId: string) {
  const entry = operations.get(requestId)
  if (entry && entry.child.stdin.writable) {
    entry.child.stdin.write(JSON.stringify({ cancel: true }) + '\n')
  }
}

function registerIpcHandlers() {
  ipcMain.handle('operation:start', (_event, { operation, params }) => {
    return startOperation(operation, params)
  })

  ipcMain.handle('operation:cancel', (_event, { requestId }: { requestId: string }) => {
    cancelOperation(requestId)
  })

  ipcMain.handle('dialog:openFile', async (_event, options: { filters?: Electron.FileFilter[]; multi?: boolean }) => {
    if (!win) return options?.multi ? [] : null
    const result = await dialog.showOpenDialog(win, {
      properties: options?.multi ? ['openFile', 'multiSelections'] : ['openFile'],
      filters: options?.filters,
    })
    if (result.canceled) return options?.multi ? [] : null
    return options?.multi ? result.filePaths : result.filePaths[0]
  })

  ipcMain.handle('dialog:openFolder', async () => {
    if (!win) return null
    const result = await dialog.showOpenDialog(win, { properties: ['openDirectory'] })
    if (result.canceled || result.filePaths.length === 0) return null
    return result.filePaths[0]
  })

  ipcMain.handle('shell:openPath', (_event, filePath: string) => {
    return shell.openPath(filePath)
  })
}

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'logo.png'),
    width: 1200,
    height: 860,
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('before-quit', () => {
  for (const entry of operations.values()) {
    entry.child.kill()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(() => {
  registerIpcHandlers()
  createWindow()
})
