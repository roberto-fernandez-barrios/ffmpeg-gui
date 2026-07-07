import { useState, type DragEvent } from 'react'
import { getDroppedPaths } from '../dragDrop'

function baseName(folderPath: string) {
  return folderPath.replace(/[\\/]+$/, '').split(/[\\/]/).pop() ?? folderPath
}

export function FolderPicker({
  label,
  value,
  onSelect,
  placeholder = 'Seleccionar o arrastrar carpeta',
}: {
  label: string
  value: string | null
  onSelect: (path: string) => void
  placeholder?: string
}) {
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    const [path] = getDroppedPaths(e.dataTransfer)
    if (path) onSelect(path)
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
          const path = await window.api.pickFolder()
          if (path) onSelect(path)
        }}
        className="w-full cursor-pointer rounded-lg bg-neutral-900 py-2 px-3 text-primary text-left truncate"
      >
        {value ? baseName(value) : placeholder}
      </button>
    </div>
  )
}
