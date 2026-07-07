import type { ReactNode } from 'react'

export function Panel({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="w-full p-4 rounded-2xl bg-neutral-700 flex flex-col gap-3">
      {title && <h2 className="text-lg text-primary font-semibold">{title}</h2>}
      {children}
    </div>
  )
}
