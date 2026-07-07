// Empaqueta logic/cli.py como un ejecutable independiente (sin depender de que
// la máquina de destino tenga Python instalado) usando PyInstaller, para que
// electron-builder pueda incluirlo como extraResource. Se ejecuta como parte
// de `npm run build`, antes de `electron-builder`.
const { spawnSync } = require('node:child_process')
const path = require('node:path')
const fs = require('node:fs')

const FRONTEND_DIR = path.join(__dirname, '..')
const REPO_ROOT = path.join(FRONTEND_DIR, '..')
const LOGIC_DIR = path.join(REPO_ROOT, 'logic')
const CLI_ENTRY = path.join(LOGIC_DIR, 'cli.py')
const DIST_DIR = path.join(FRONTEND_DIR, 'backend-dist')
const WORK_DIR = path.join(REPO_ROOT, 'build', 'cli_bridge')

function resolvePython() {
  const venvPython = path.join(REPO_ROOT, 'venv', 'Scripts', 'python.exe')
  if (fs.existsSync(venvPython)) return venvPython

  for (const candidate of ['python', 'python3', 'py']) {
    const probe = spawnSync(candidate, ['--version'])
    if (!probe.error) return candidate
  }

  console.error('No se encontró un intérprete de Python para construir el backend empaquetado.')
  process.exit(1)
}

function ensurePyInstaller(python) {
  const probe = spawnSync(python, ['-m', 'PyInstaller', '--version'])
  if (probe.status !== 0) {
    console.error('PyInstaller no está instalado en el entorno de Python usado para el build.')
    console.error(`Instálalo con: ${python} -m pip install pyinstaller`)
    process.exit(1)
  }
}

function main() {
  const python = resolvePython()
  console.log(`Usando intérprete de Python: ${python}`)
  ensurePyInstaller(python)

  const args = [
    '-m',
    'PyInstaller',
    '--onefile',
    '--noconsole',
    '--name',
    'ffmpeg-cli-bridge',
    '--distpath',
    DIST_DIR,
    '--workpath',
    WORK_DIR,
    '--specpath',
    WORK_DIR,
    '--paths',
    LOGIC_DIR,
    CLI_ENTRY,
  ]

  const result = spawnSync(python, args, { stdio: 'inherit' })
  if (result.status !== 0) {
    console.error('Fallo al construir el backend empaquetado con PyInstaller.')
    process.exit(result.status ?? 1)
  }

  const exePath = path.join(DIST_DIR, 'ffmpeg-cli-bridge.exe')
  if (!fs.existsSync(exePath)) {
    console.error(`PyInstaller terminó sin errores pero no se encontró el ejecutable esperado en ${exePath}`)
    process.exit(1)
  }

  console.log(`Backend empaquetado en: ${exePath}`)
}

main()
