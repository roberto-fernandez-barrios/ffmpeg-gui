import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { TextField } from '../components/fields'
import { OperationForm } from '../components/OperationForm'
import { useTaskQueue } from '../hooks/useTaskQueue'
import { baseName } from '../dragDrop'

export default function LimitKps() {
  const [video, setVideo] = useState<string | null>(null)
  const [bitrate, setBitrate] = useState('57M')
  const [maxrate, setMaxrate] = useState('60M')

  const { tasks, submit, cancel } = useTaskQueue()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return

    submit(`Limitación: ${baseName(video)}`, 'limit_kbps', {
      video,
      bitrate,
      maxrate,
      format: 'mp4',
    })
  }

  return (
    <OperationForm
      onSubmit={handleSubmit}
      submitLabel="Limitar Kps"
      canSubmit={Boolean(video)}
      disabledHint="Selecciona un video primero."
      tasks={tasks}
      onCancel={cancel}
    >
      <Panel title="Seleccionar video">
        <VideoPicker label="Video de entrada" value={video} onSelect={setVideo} />
      </Panel>

      <Panel title="Parámetros de limitación">
        <TextField label="Bitrate de video (k/M/G)" value={bitrate} onChange={setBitrate} />
        <TextField label="Maxrate (k/M/G)" value={maxrate} onChange={setMaxrate} />
      </Panel>
    </OperationForm>
  )
}
