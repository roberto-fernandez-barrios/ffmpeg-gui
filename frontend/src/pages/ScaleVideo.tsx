import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { TextField, SelectField } from '../components/fields'
import { OperationForm } from '../components/OperationForm'
import { useTaskQueue } from '../hooks/useTaskQueue'
import { baseName } from '../dragDrop'

const PRESETS = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

export default function ScaleVideo() {
  const [video, setVideo] = useState<string | null>(null)
  const [width, setWidth] = useState('2520')
  const [height, setHeight] = useState('5376')
  const [preset, setPreset] = useState('slow')
  const [crf, setCrf] = useState('19')

  const { tasks, submit, cancel } = useTaskQueue()

  const dimensionsValid = /^\d+$/.test(width) && /^\d+$/.test(height)
  const canSubmit = Boolean(video) && dimensionsValid

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    submit(`Reescalado: ${baseName(video!)}`, 'scale_video', {
      video,
      width,
      height,
      preset,
      crf,
      format: 'mp4',
    })
  }

  return (
    <OperationForm
      onSubmit={handleSubmit}
      submitLabel="Reescalar Video"
      canSubmit={canSubmit}
      disabledHint={!video ? 'Selecciona un video primero.' : 'El ancho y el alto deben ser números.'}
      tasks={tasks}
      onCancel={cancel}
    >
      <Panel title="Seleccionar video">
        <VideoPicker label="Video de entrada" value={video} onSelect={setVideo} />
      </Panel>

      <Panel title="Parámetros de escalado">
        <TextField label="Ancho deseado (px)" value={width} onChange={setWidth} />
        <TextField label="Alto deseado (px)" value={height} onChange={setHeight} />
        <SelectField label="Preset" value={preset} onChange={setPreset} options={PRESETS} />
        <TextField label="CRF" value={crf} onChange={setCrf} />
      </Panel>
    </OperationForm>
  )
}
