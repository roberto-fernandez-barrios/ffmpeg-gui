import type { ReactNode } from 'react'

const ROW = 'w-full p-3 rounded-xl flex flex-row items-center justify-between gap-3 text-base bg-neutral-800'

export function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}) {
  return (
    <div className={ROW}>
      <label className="text-neutral-200">{label}</label>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-32 text-right bg-transparent outline-none text-primary"
      />
    </div>
  )
}

export function NumberField({
  label,
  value,
  onChange,
  min,
}: {
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
}) {
  return (
    <div className={ROW}>
      <label className="text-neutral-200">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        onChange={(e) => onChange(e.target.valueAsNumber || 0)}
        className="w-24 text-right bg-transparent outline-none text-primary [&::-webkit-inner-spin-button]:appearance-none"
      />
    </div>
  )
}

export function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
}) {
  return (
    <div className={ROW}>
      <label className="text-neutral-200">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-neutral-800 text-primary text-right outline-none cursor-pointer"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-neutral-800 text-white">
            {option}
          </option>
        ))}
      </select>
    </div>
  )
}

export function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <label className={`${ROW} cursor-pointer`}>
      <span className="text-neutral-200">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-5 h-5 cursor-pointer accent-primary"
      />
    </label>
  )
}

export function SubmitButton({ children }: { children: ReactNode }) {
  return (
    <button
      type="submit"
      className="w-full p-3 cursor-pointer rounded-full text-xl font-medium text-black bg-primary hover:opacity-90 transition-opacity"
    >
      {children}
    </button>
  )
}
