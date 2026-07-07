import { useState, type FormEvent } from 'react'
import { Panel } from '../components/Panel'
import { VideoPicker } from '../components/FilePicker'
import { NumberField, SubmitButton } from '../components/fields'
import { TaskList } from '../components/TaskList'
import { useTaskQueue } from '../hooks/useTaskQueue'

export default function TrimVideo() {
  const [video, setVideo] = useState<string | null>(null)
  const [top, setTop] = useState(0)
  const [bottom, setBottom] = useState(0)
  const [left, setLeft] = useState(0)
  const [right, setRight] = useState(0)
  const [fadeIn, setFadeIn] = useState(0)
  const [fadeOut, setFadeOut] = useState(0)

  const { tasks, submit, cancel } = useTaskQueue()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!video) return

    submit(`Recorte: ${video.split(/[\\/]/).pop()}`, 'crop_video', {
      video,
      top,
      bottom,
      left,
      right,
      fadeIn,
      fadeOut,
      format: 'mp4',
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
        <Panel title="Seleccionar video">
          <VideoPicker label="Video de entrada" value={video} onSelect={setVideo} />
        </Panel>

        <Panel title="Parámetros de recorte">
          <NumberField label="Recortar arriba (px)" value={top} onChange={setTop} min={0} />
          <NumberField label="Recortar abajo (px)" value={bottom} onChange={setBottom} min={0} />
          <NumberField label="Recortar izquierda (px)" value={left} onChange={setLeft} min={0} />
          <NumberField label="Recortar derecha (px)" value={right} onChange={setRight} min={0} />
        </Panel>

        <Panel title="Fundidos a negro">
          <NumberField label="Fade in al inicio (segundos)" value={fadeIn} onChange={setFadeIn} min={0} />
          <NumberField label="Fade out al final (segundos)" value={fadeOut} onChange={setFadeOut} min={0} />
        </Panel>

        <SubmitButton>Recortar Video</SubmitButton>
      </form>

      <TaskList tasks={tasks} onCancel={cancel} />
    </div>
  )
}
