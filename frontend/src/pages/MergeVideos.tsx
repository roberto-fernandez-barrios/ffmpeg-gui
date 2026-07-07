import { useEffect, useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { FolderPicker } from '../components/FolderPicker'
import { TextField, SelectField, SubmitButton } from '../components/fields'
import { ProgressBar } from '../components/ProgressBar'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

const MODES: Record<string, 'fast' | 'compatible'> = {
  'Rápido (sin recodificar)': 'fast',
  'Compatible (recodificar)': 'compatible',
}

const PRESETS = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

const VIDEO_FILTERS = [{ name: 'Videos', extensions: ['mp4', 'avi', 'mkv', 'mov'] }]

function baseName(filePath: string) {
  return filePath.split(/[\\/]/).pop() ?? filePath
}

interface PairTask {
  pairIndex: number
  label: string
  status: 'running' | 'done' | 'error'
  progress: number
  output: string | null
  error: string | null
}

function upsertPair(prev: PairTask[], pairIndex: number, patch: Partial<PairTask>): PairTask[] {
  const existingIndex = prev.findIndex((p) => p.pairIndex === pairIndex)
  if (existingIndex === -1) {
    const base: PairTask = { pairIndex, label: '', status: 'running', progress: 0, output: null, error: null }
    return [...prev, { ...base, ...patch }].sort((a, b) => a.pairIndex - b.pairIndex)
  }
  const next = [...prev]
  next[existingIndex] = { ...next[existingIndex], ...patch }
  return next
}

export default function MergeVideos() {
  const [videos, setVideos] = useState<string[]>([])
  const [modeLabel, setModeLabel] = useState('Rápido (sin recodificar)')
  const [outputName, setOutputName] = useState('')
  const [preset, setPreset] = useState('slow')
  const [crf, setCrf] = useState('19')

  const { tasks, submit, cancel } = useTaskQueue()

  const [folder1, setFolder1] = useState<string | null>(null)
  const [folder2, setFolder2] = useState<string | null>(null)
  const [autoRequestId, setAutoRequestId] = useState<string | null>(null)
  const [autoPairs, setAutoPairs] = useState<PairTask[]>([])
  const [autoError, setAutoError] = useState<string | null>(null)

  const mode = MODES[modeLabel]
  const compatible = mode === 'compatible'

  useEffect(() => {
    if (!autoRequestId) return
    return window.api.onOperationMessage(({ requestId, data }) => {
      if (requestId !== autoRequestId) return
      if (data.type === 'pair_progress') {
        setAutoPairs((prev) =>
          upsertPair(prev, data.pairIndex, { progress: data.percent, label: data.label, status: 'running' }),
        )
      } else if (data.type === 'pair_done') {
        setAutoPairs((prev) =>
          upsertPair(prev, data.pairIndex, {
            status: data.success ? 'done' : 'error',
            progress: data.success ? 100 : 0,
            output: data.output,
            error: data.error,
            label: data.label,
          }),
        )
      } else if (data.type === 'result' && !data.success && (!data.pairs || data.pairs.length === 0)) {
        setAutoError(data.error ?? 'No se encontraron coincidencias.')
      }
    })
  }, [autoRequestId])

  const addVideos = async () => {
    const paths = await window.api.pickFiles({ filters: VIDEO_FILTERS })
    if (!paths.length) return
    const existing = new Set(videos)
    const additions = paths.filter((p) => !existing.has(p))
    setVideos((prev) => [...prev, ...additions])
  }

  const removeVideo = (path: string) => setVideos((prev) => prev.filter((v) => v !== path))
  const clearVideos = () => setVideos([])

  const moveVideo = (index: number, direction: -1 | 1) => {
    setVideos((prev) => {
      const target = index + direction
      if (target < 0 || target >= prev.length) return prev
      const next = [...prev]
      ;[next[index], next[target]] = [next[target], next[index]]
      return next
    })
  }

  const handleManualSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (videos.length < 2) return

    submit(
      mode === 'fast' ? `Unión rápida: ${videos.length} videos` : `Unión compatible: ${videos.length} videos`,
      'merge_videos',
      { videos, mode, outputName: outputName || undefined, preset, crf, format: 'mp4' },
    )
  }

  const handleAutoMerge = async () => {
    if (!folder1 || !folder2) return
    setAutoPairs([])
    setAutoError(null)
    const { requestId } = await window.api.startOperation('merge_auto', {
      folder1,
      folder2,
      mode,
      preset,
      crf,
      format: 'mp4',
    })
    setAutoRequestId(requestId)
  }

  const autoRunning = autoPairs.some((p) => p.status === 'running')

  return (
    <div className="flex flex-col gap-6">
      <Panel title="Unión manual de videos">
        <div className="flex flex-row justify-between items-center">
          <span className="text-neutral-200">Videos seleccionados: {videos.length}</span>
          <div className="flex flex-row gap-2">
            <button type="button" onClick={addVideos} className="text-primary cursor-pointer text-sm underline">
              Añadir videos
            </button>
            {videos.length > 0 && (
              <button type="button" onClick={clearVideos} className="text-neutral-400 cursor-pointer text-sm underline">
                Limpiar lista
              </button>
            )}
          </div>
        </div>

        {videos.length > 0 && (
          <div className="flex flex-col gap-1">
            {videos.map((video, index) => (
              <div key={video} className="flex flex-row items-center gap-2 p-2 rounded-lg bg-neutral-800">
                <span className="flex-1 truncate text-sm">{baseName(video)}</span>
                <button type="button" onClick={() => moveVideo(index, -1)} className="text-neutral-400 hover:text-white cursor-pointer text-sm">
                  Subir
                </button>
                <button type="button" onClick={() => moveVideo(index, 1)} className="text-neutral-400 hover:text-white cursor-pointer text-sm">
                  Bajar
                </button>
                <button type="button" onClick={() => removeVideo(video)} className="text-red-400 hover:text-red-300 cursor-pointer text-sm">
                  Quitar
                </button>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Emparejado automático por carpetas">
        <FolderPicker label="Carpeta 1 (Video Campaña)" value={folder1} onSelect={setFolder1} />
        <FolderPicker label="Carpeta 2 (Lookbook Campaña)" value={folder2} onSelect={setFolder2} />
        <p className="text-sm text-neutral-400">
          Empareja por resolución y distingue automáticamente la variante "sin logo" si aparece en el nombre del
          archivo.
        </p>
        <button
          type="button"
          onClick={handleAutoMerge}
          disabled={!folder1 || !folder2 || autoRunning}
          className="w-full p-2 cursor-pointer rounded-xl text-primary bg-neutral-800 hover:bg-neutral-900 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Fusionar carpetas por resolución
        </button>

        {autoError && <span className="text-sm text-red-400">{autoError}</span>}

        {autoPairs.length > 0 && (
          <div className="flex flex-col gap-2">
            {autoPairs.map((pair) => (
              <div key={pair.pairIndex} className="p-3 rounded-xl bg-neutral-800 flex flex-col gap-2">
                <span className="truncate text-sm">{pair.label}</span>
                {pair.status === 'running' && <ProgressBar percent={pair.progress} />}
                {pair.status === 'done' && pair.output && (
                  <button
                    type="button"
                    onClick={() => window.api.openPath(pair.output!)}
                    className="text-left text-primary underline text-sm truncate cursor-pointer"
                  >
                    Completado: {baseName(pair.output)}
                  </button>
                )}
                {pair.status === 'error' && <span className="text-sm text-red-400">Error: {pair.error}</span>}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <form onSubmit={handleManualSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Configuración de unión">
          <SelectField label="Modo de unión" value={modeLabel} onChange={setModeLabel} options={Object.keys(MODES)} />
          <TextField label="Nombre de salida (opcional)" value={outputName} onChange={setOutputName} />
          {compatible && (
            <>
              <SelectField label="Preset (modo compatible)" value={preset} onChange={setPreset} options={PRESETS} />
              <TextField label="CRF (modo compatible)" value={crf} onChange={setCrf} />
            </>
          )}
        </Panel>

        <SubmitButton>Unir lista manual</SubmitButton>
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
