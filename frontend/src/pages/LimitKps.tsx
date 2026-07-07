import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { TextField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

export default function LimitKps() {
  const [video, setVideo] = useState<string | null>(null)
  const [bitrate, setBitrate] = useState('57M')
  const [maxrate, setMaxrate] = useState('60M')

  const { tasks, submit, cancel } = useTaskQueue()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return

    submit(`Limitación: ${video.split(/[\\/]/).pop()}`, 'limit_kbps', {
      video,
      bitrate,
      maxrate,
      format: 'mp4',
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Seleccionar video">
          <VideoPicker label="Video de entrada" value={video} onSelect={setVideo} />
        </Panel>

        <Panel title="Parámetros de limitación">
          <TextField label="Bitrate de video (k/M/G)" value={bitrate} onChange={setBitrate} />
          <TextField label="Maxrate (k/M/G)" value={maxrate} onChange={setMaxrate} />
        </Panel>

        <SubmitButton disabled={!video}>Limitar Kps</SubmitButton>
        {!video && <p className="text-sm text-neutral-400 -mt-2">Selecciona un video primero.</p>}
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
