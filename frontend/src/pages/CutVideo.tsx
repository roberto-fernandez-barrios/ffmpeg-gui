import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { TextField, NumberField, SelectField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

const MODES: Record<string, 'time' | 'frames'> = {
  Tiempo: 'time',
  Frames: 'frames',
}

export default function CutVideo() {
  const [video, setVideo] = useState<string | null>(null)
  const [modeLabel, setModeLabel] = useState('Frames')
  const [start, setStart] = useState('0')
  const [fps, setFps] = useState('30')
  const [duration, setDuration] = useState('')
  const [endTime, setEndTime] = useState('')
  const [fadeIn, setFadeIn] = useState(0)
  const [fadeOut, setFadeOut] = useState(0)

  const { tasks, submit, cancel } = useTaskQueue()

  const cutMode = MODES[modeLabel]

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return

    submit(`Corte: ${video.split(/[\\/]/).pop()}`, 'cut_video', {
      video,
      cutMode,
      start,
      fps: cutMode === 'frames' ? fps : undefined,
      duration: duration || undefined,
      endTime: cutMode === 'time' ? endTime || undefined : undefined,
      fadeIn,
      fadeOut,
      format: 'mp4',
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Seleccionar video">
          <VideoPicker label="Video" value={video} onSelect={setVideo} />
        </Panel>

        <Panel title="Parámetros de corte">
          <SelectField label="Modo de corte" value={modeLabel} onChange={setModeLabel} options={['Frames', 'Tiempo']} />
          <TextField
            label={cutMode === 'time' ? 'Inicio (segundos o hh:mm:ss)' : 'Inicio (frames)'}
            value={start}
            onChange={setStart}
          />
          {cutMode === 'frames' && <TextField label="FPS (del video de entrada)" value={fps} onChange={setFps} />}
          <TextField
            label={cutMode === 'time' ? 'Duración (segundos, opcional)' : 'Cantidad de frames (opcional)'}
            value={duration}
            onChange={setDuration}
          />
          {cutMode === 'time' && (
            <TextField label="Tiempo final (opcional)" value={endTime} onChange={setEndTime} />
          )}
        </Panel>

        <Panel title="Fundidos a negro">
          <NumberField label="Fade in al inicio (segundos)" value={fadeIn} onChange={setFadeIn} min={0} />
          <NumberField label="Fade out al final (segundos)" value={fadeOut} onChange={setFadeOut} min={0} />
        </Panel>

        <SubmitButton>Cortar Video</SubmitButton>
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
