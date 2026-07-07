import { useState, type DragEvent } from 'react'
import { getDroppedPaths, extensionOf } from '../dragDrop'

const VIDEO_FILTERS = [{ name: 'Videos', extensions: ['mp4', 'avi', 'mkv', 'mov'] }]
const AUDIO_FILTERS = [{ name: 'Audio', extensions: ['mp3', 'wav', 'aac'] }]

function baseName(filePath: string) {
  return filePath.split(/[\\/]/).pop() ?? filePath
}

function FilePickerBase({
  label,
  value,
  onSelect,
  filters,
  placeholder,
}: {
  label: string
  value: string | null
  onSelect: (path: string) => void
  filters: { name: string; extensions: string[] }[]
  placeholder: string
}) {
  const [isDragOver, setIsDragOver] = useState(false)
  const allowedExtensions = filters.flatMap((f) => f.extensions.map((ext) => ext.toLowerCase()))

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    const match = getDroppedPaths(e.dataTransfer).find((path) => allowedExtensions.includes(extensionOf(path)))
    if (match) onSelect(match)
  }

  return (
    <div
      className={`w-full p-3 rounded-xl flex flex-col gap-2 bg-neutral-800 transition-colors ${
        isDragOver ? 'ring-2 ring-primary' : ''
      }`}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      <span className="text-neutral-200">{label}</span>
      <button
        type="button"
        onClick={async () => {
          const path = await window.api.pickFile({ filters })
          if (path) onSelect(path)
        }}
        className="w-full cursor-pointer rounded-lg bg-neutral-900 py-2 px-3 text-primary text-left truncate"
      >
        {value ? baseName(value) : placeholder}
      </button>
    </div>
  )
}

export function VideoPicker(props: { label: string; value: string | null; onSelect: (path: string) => void }) {
  return <FilePickerBase {...props} filters={VIDEO_FILTERS} placeholder="Seleccionar o arrastrar video" />
}

export function AudioPicker(props: { label: string; value: string | null; onSelect: (path: string) => void }) {
  return <FilePickerBase {...props} filters={AUDIO_FILTERS} placeholder="Seleccionar o arrastrar audio" />
}
