import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker, AudioPicker } from '../components/FilePicker'
import { SelectField } from '../components/fields'
import { OperationForm } from '../components/OperationForm'
import { useTaskQueue } from '../hooks/useTaskQueue'
import { baseName } from '../dragDrop'

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
  const canSubmit = Boolean(video) && (!needsAudio || Boolean(audio))

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return
    if (needsAudio && !audio) return

    submit(`${LABELS[mode]}: ${baseName(video)}`, 'audio_edit', {
      mode,
      video,
      audio: needsAudio ? audio : undefined,
      format: 'mp4',
    })
  }

  return (
    <OperationForm
      onSubmit={handleSubmit}
      submitLabel="Procesar"
      canSubmit={canSubmit}
      disabledHint={!video ? 'Selecciona un video primero.' : 'Selecciona un archivo de audio.'}
      tasks={tasks}
      onCancel={cancel}
    >
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
    </OperationForm>
  )
}
