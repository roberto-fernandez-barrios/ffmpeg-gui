function baseName(folderPath: string) {
  return folderPath.replace(/[\\/]+$/, '').split(/[\\/]/).pop() ?? folderPath
}

export function FolderPicker({
  label,
  value,
  onSelect,
  placeholder = 'Seleccionar carpeta',
}: {
  label: string
  value: string | null
  onSelect: (path: string) => void
  placeholder?: string
}) {
  return (
    <div className="w-full p-3 rounded-xl flex flex-col gap-2 bg-neutral-800">
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
