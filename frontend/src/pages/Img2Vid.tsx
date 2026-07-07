import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { FolderPicker } from '../components/FolderPicker'
import { AudioPicker } from '../components/FilePicker'
import { TextField, NumberField, SelectField, CheckboxField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

const FORMATS = [
  'mp4 (H.264 16-bit)',
  'mp4 (H.265 16-bit)',
  'mp4 (H.265 10-bit)',
  'mp4 (H.264 10-bit)',
  'mp4 (H.264 8-bit)',
  'mp4 (H.265 8-bit)',
  'avi',
  'mkv',
  'mov',
]

const YUV_FORMATS = ['yuv420p', 'yuv422p', 'yuv444p']

export default function Img2Vid() {
  const [folder, setFolder] = useState<string | null>(null)
  const [audio, setAudio] = useState<string | null>(null)
  const [fps, setFps] = useState('30')
  const [crf, setCrf] = useState('19')
  const [fadeIn, setFadeIn] = useState(0)
  const [fadeOut, setFadeOut] = useState(0)
  const [prioritizeAudio, setPrioritizeAudio] = useState(false)
  const [format, setFormat] = useState(FORMATS[4])
  const [pixFmt, setPixFmt] = useState(YUV_FORMATS[0])

  const { tasks, submit, cancel } = useTaskQueue()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!folder) return

    submit(`Conversión: ${folder.split(/[\\/]/).pop()}`, 'img2vid', {
      folder,
      fps,
      audioPath: audio,
      format,
      crf,
      fadeIn,
      fadeOut,
      pixFmt,
      prioritizeAudio,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Imágenes de origen">
          <FolderPicker label="Carpeta con imágenes" value={folder} onSelect={setFolder} />
        </Panel>

        <Panel title="Configuración de conversión">
          <TextField label="FPS (frames por segundo)" value={fps} onChange={setFps} />
          <TextField label="CRF" value={crf} onChange={setCrf} />
          <NumberField label="Fade In (segundos)" value={fadeIn} onChange={setFadeIn} min={0} />
          <NumberField label="Fade Out (segundos)" value={fadeOut} onChange={setFadeOut} min={0} />
          <AudioPicker label="Archivo de audio (opcional)" value={audio} onSelect={setAudio} />
          {audio && (
            <button
              type="button"
              onClick={() => setAudio(null)}
              className="text-sm text-neutral-400 hover:text-neutral-200 text-left cursor-pointer"
            >
              Limpiar audio
            </button>
          )}
          <CheckboxField label="Priorizar audio" checked={prioritizeAudio} onChange={setPrioritizeAudio} />
          <SelectField label="Formato de salida" value={format} onChange={setFormat} options={FORMATS} />
          <SelectField label="Formato YUV" value={pixFmt} onChange={setPixFmt} options={YUV_FORMATS} />
        </Panel>

        <SubmitButton disabled={!folder}>Convertir imágenes en video</SubmitButton>
        {!folder && <p className="text-sm text-neutral-400 -mt-2">Selecciona una carpeta de imágenes primero.</p>}
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
