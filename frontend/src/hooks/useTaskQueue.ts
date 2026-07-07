import { useCallback, useEffect, useRef, useState } from 'react'
import type { Task } from '../types/task'
import type { OperationMessage } from '../../electron/preload'

function applyMessage(task: Task, data: OperationMessage): Task {
  if (data.type === 'progress') {
    return { ...task, progress: data.percent }
  }

  if (data.type === 'result') {
    if (data.cancelled) {
      return { ...task, status: 'cancelled', progress: 0 }
    }
    if (data.success) {
      return { ...task, status: 'done', progress: 100, output: data.output ?? null }
    }
    return { ...task, status: 'error', error: data.error ?? 'Error desconocido.' }
  }

  return task
}

export function useTaskQueue() {
  const [tasks, setTasks] = useState<Task[]>([])
  // Un requestId puede recibir su primer mensaje antes de que termine el
  // `invoke` que lo crea (la fila de tarea aún no existe). Se guarda en buffer
  // para no perder ese mensaje.
  const pendingMessages = useRef(new Map<string, OperationMessage[]>())

  useEffect(() => {
    return window.api.onOperationMessage(({ requestId, data }) => {
      setTasks((prev) => {
        const index = prev.findIndex((task) => task.id === requestId)
        if (index === -1) {
          const queue = pendingMessages.current.get(requestId) ?? []
          queue.push(data)
          pendingMessages.current.set(requestId, queue)
          return prev
        }
        const next = [...prev]
        next[index] = applyMessage(next[index], data)
        return next
      })
    })
  }, [])

  const submit = useCallback(async (name: string, operation: string, params: unknown) => {
    const { requestId } = await window.api.startOperation(operation, params)
    setTasks((prev) => {
      let task: Task = { id: requestId, name, status: 'running', progress: 0, output: null, error: null }
      const buffered = pendingMessages.current.get(requestId)
      if (buffered) {
        for (const data of buffered) task = applyMessage(task, data)
        pendingMessages.current.delete(requestId)
      }
      return [task, ...prev]
    })
  }, [])

  const cancel = useCallback((taskId: string) => {
    window.api.cancelOperation(taskId)
  }, [])

  return { tasks, submit, cancel }
}
