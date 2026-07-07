import { useEffect, useState } from 'react'

export function DependencyBanner() {
  const [missing, setMissing] = useState<string[]>([])

  useEffect(() => {
    let cancelled = false
    window.api
      .checkDependencies()
      .then(({ ffmpeg, ffprobe }) => {
        if (cancelled) return
        const names: string[] = []
        if (!ffmpeg) names.push('ffmpeg')
        if (!ffprobe) names.push('ffprobe')
        setMissing(names)
      })
      .catch(() => {
        // Si falla la comprobación (IPC caído, etc.), no bloqueamos la UI con
        // un aviso falso de dependencias ausentes.
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (missing.length === 0) return null

  return (
    <div className="w-full mb-4 p-3 rounded-xl bg-red-950 border border-red-800 text-red-200 text-sm">
      No se encontró <strong>{missing.join(' y ')}</strong> en el PATH del sistema. Las conversiones fallarán hasta
      que instales FFmpeg (incluye ffmpeg y ffprobe) desde{' '}
      <button
        type="button"
        onClick={() => window.api.openExternal('https://ffmpeg.org/download.html')}
        className="underline cursor-pointer"
      >
        ffmpeg.org
      </button>{' '}
      y lo añadas al PATH, luego reinicia la aplicación.
    </div>
  )
}
