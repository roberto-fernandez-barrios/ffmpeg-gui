import type { Task } from '../types/task'
import { ProgressBar } from './ProgressBar'

function baseName(filePath: string) {
  return filePath.split(/[\\/]/).pop() ?? filePath
}

export function TaskList({ tasks, onCancel }: { tasks: Task[]; onCancel: (id: string) => void }) {
  if (tasks.length === 0) return null

  return (
    <div className="w-full p-4 rounded-2xl bg-neutral-700 flex flex-col gap-2">
      <h2 className="text-lg text-primary font-semibold">Tareas</h2>
      {tasks.map((task) => (
        <div key={task.id} className="w-full p-3 rounded-xl bg-neutral-800 flex flex-col gap-2">
          <div className="flex flex-row justify-between items-center gap-2">
            <span className="truncate">{task.name}</span>
            {task.status === 'running' && (
              <button
                type="button"
                onClick={() => onCancel(task.id)}
                className="text-sm text-red-400 hover:text-red-300 cursor-pointer shrink-0"
              >
                Cancelar
              </button>
            )}
          </div>

          {task.status === 'running' && <ProgressBar percent={task.progress} />}

          {task.status === 'done' && task.output && (
            <button
              type="button"
              onClick={() => window.api.openPath(task.output!)}
              className="text-left text-primary underline text-sm truncate cursor-pointer"
            >
              Completado: {baseName(task.output)}
            </button>
          )}

          {task.status === 'cancelled' && <span className="text-sm text-neutral-400">Cancelado</span>}
          {task.status === 'error' && <span className="text-sm text-red-400">Error: {task.error}</span>}
        </div>
      ))}
    </div>
  )
}
