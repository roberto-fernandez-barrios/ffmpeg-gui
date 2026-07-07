import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker, AudioPicker } from '../components/FilePicker'
import { SelectField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

const OPERATIONS: Record<string, 'add' | 'remove' | 'replace'> = {
  'Añadir audio': 'add',
  'Quitar audio': 'remove',
  'Sustituir audio': 'replace',
}

const LABELS: Record<'add' | 'remove' | 'replace', string> = {
  add: 'Añadir audio',
  remove: 'Quitar audio',
  replace: 'Sustituir audio',
}

export default function EditAudio() {
  const [video, setVideo] = useState<string | null>(null)
  const [audio, setAudio] = useState<string | null>(null)
  const [operationLabel, setOperationLabel] = useState('Añadir audio')

  const { tasks, submit, cancel } = useTaskQueue()

  const mode = OPERATIONS[operationLabel]
  const needsAudio = mode !== 'remove'

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return
    if (needsAudio && !audio) return

    submit(`${LABELS[mode]}: ${video.split(/[\\/]/).pop()}`, 'audio_edit', {
      mode,
      video,
      audio: needsAudio ? audio : undefined,
      format: 'mp4',
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Seleccionar video">
          <VideoPicker label="Video" value={video} onSelect={setVideo} />
        </Panel>

        <Panel title="Operación de edición de audio">
          <SelectField
            label="Selecciona la operación"
            value={operationLabel}
            onChange={setOperationLabel}
            options={Object.keys(OPERATIONS)}
          />
          {needsAudio && <AudioPicker label="Audio" value={audio} onSelect={setAudio} />}
        </Panel>

        <SubmitButton>Procesar</SubmitButton>
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
