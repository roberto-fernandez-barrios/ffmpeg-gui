import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { TextField, SelectField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

const PRESETS = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

export default function ScaleVideo() {
  const [video, setVideo] = useState<string | null>(null)
  const [width, setWidth] = useState('2520')
  const [height, setHeight] = useState('5376')
  const [preset, setPreset] = useState('slow')
  const [crf, setCrf] = useState('19')

  const { tasks, submit, cancel } = useTaskQueue()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return
    if (!/^\d+$/.test(width) || !/^\d+$/.test(height)) return

    submit(`Reescalado: ${video.split(/[\\/]/).pop()}`, 'scale_video', {
      video,
      width,
      height,
      preset,
      crf,
      format: 'mp4',
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Seleccionar video">
          <VideoPicker label="Video de entrada" value={video} onSelect={setVideo} />
        </Panel>

        <Panel title="Parámetros de escalado">
          <TextField label="Ancho deseado (px)" value={width} onChange={setWidth} />
          <TextField label="Alto deseado (px)" value={height} onChange={setHeight} />
          <SelectField label="Preset" value={preset} onChange={setPreset} options={PRESETS} />
          <TextField label="CRF" value={crf} onChange={setCrf} />
        </Panel>

        <SubmitButton>Reescalar Video</SubmitButton>
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
