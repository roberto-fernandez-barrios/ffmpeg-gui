import type { FormEvent, ReactNode } from 'react'
import { SubmitButton } from './fields'
import { TaskList } from './TaskList'
import type { Task } from '../types/task'

/**
 * Envoltorio compartido por las páginas de una sola operación (Cortar,
 * Limitar Kps, Escalar, Recortar, Editar audio): formulario + botón de
 * envío con su aviso de "falta X" + lista de tareas. Cada página aporta
 * sus propios <Panel> como children; solo se comparte el armazón.
 */
export function OperationForm({
  onSubmit,
  submitLabel,
  canSubmit,
  disabledHint,
  tasks,
  onCancel,
  children,
}: {
  onSubmit: (e: FormEvent) => void
  submitLabel: string
  canSubmit: boolean
  disabledHint: string
  tasks: Task[]
  onCancel: (id: string) => void
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={onSubmit} className="w-full flex flex-col gap-4">
        {children}
        <SubmitButton disabled={!canSubmit}>{submitLabel}</SubmitButton>
        {!canSubmit && <p className="text-sm text-neutral-400 -mt-2">{disabledHint}</p>}
      </form>

      <TaskList tasks={tasks} onCancel={onCancel} />
    </div>
  )
}
