export function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="w-full h-2 rounded-full bg-neutral-900 overflow-hidden">
      <div
        className="h-full bg-primary transition-[width] duration-200"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  )
}
