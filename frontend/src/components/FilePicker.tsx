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
  return (
    <div className="w-full p-3 rounded-xl flex flex-col gap-2 bg-neutral-800">
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
  return <FilePickerBase {...props} filters={VIDEO_FILTERS} placeholder="Seleccionar video" />
}

export function AudioPicker(props: { label: string; value: string | null; onSelect: (path: string) => void }) {
  return <FilePickerBase {...props} filters={AUDIO_FILTERS} placeholder="Seleccionar archivo de audio" />
}
