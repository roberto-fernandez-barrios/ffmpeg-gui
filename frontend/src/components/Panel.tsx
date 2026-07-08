import type { ReactNode } from 'react'

export function Panel({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="w-full p-3 rounded-2xl bg-neutral-700 border border-white/5 shadow-lg shadow-black/20 flex flex-col gap-2">
      {title && <h2 className="text-lg text-primary font-semibold">{title}</h2>}
      {children}
    </div>
  )
}
