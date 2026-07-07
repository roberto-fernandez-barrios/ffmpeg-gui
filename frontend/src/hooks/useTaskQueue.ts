import { useCallback, useEffect, useRef, useState } from 'react'
import type { Task } from '../types/task'
import type { OperationMessage } from '../../electron/preload'

// Cuántas operaciones ffmpeg pueden correr a la vez. Cada proceso ffmpeg ya
// satura varios núcleos por sí solo al codificar, así que lanzar muchos en
// paralelo compite por CPU en vez de acelerar nada; el resto espera en cola
// y se muestra como "pending" en la UI.
const MAX_CONCURRENT = 2

interface QueuedSubmission {
  id: string
  name: string
  operation: string
  params: unknown
}

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
  // `invoke` que lo crea (la tarea aún no se ha vinculado al requestId real).
  // Se guarda en buffer para no perder ese mensaje.
  const pendingMessages = useRef(new Map<string, OperationMessage[]>())

  // Submissions que superan MAX_CONCURRENT esperan aquí hasta que se libera
  // un hueco.
  const queue = useRef<QueuedSubmission[]>([])
  const activeCount = useRef(0)

  // taskId (estable desde el submit) <-> requestId (solo existe una vez que
  // el backend confirma el arranque real de la operación).
  const requestIdToTaskId = useRef(new Map<string, string>())
  const taskIdToRequestId = useRef(new Map<string, string>())

  const dispatchRef = useRef<(sub: QueuedSubmission) => void>(() => {})

  const runNext = useCallback(() => {
    if (activeCount.current >= MAX_CONCURRENT) return
    const next = queue.current.shift()
    if (!next) return
    activeCount.current += 1
    dispatchRef.current(next)
  }, [])

  const finishSlot = useCallback(() => {
    activeCount.current = Math.max(0, activeCount.current - 1)
    runNext()
  }, [runNext])

  const dispatch = useCallback(
    async (sub: QueuedSubmission) => {
      setTasks((prev) => prev.map((t) => (t.id === sub.id ? { ...t, status: 'running' } : t)))
      try {
        const { requestId } = await window.api.startOperation(sub.operation, sub.params)
        requestIdToTaskId.current.set(requestId, sub.id)
        taskIdToRequestId.current.set(sub.id, requestId)

        const buffered = pendingMessages.current.get(requestId)
        if (buffered) {
          pendingMessages.current.delete(requestId)
          setTasks((prev) =>
            prev.map((t) => (t.id === sub.id ? buffered.reduce(applyMessage, t) : t)),
          )
          if (buffered.some((m) => m.type === 'result')) finishSlot()
        }
      } catch (err) {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === sub.id
              ? {
                  ...t,
                  status: 'error',
                  error: err instanceof Error ? err.message : 'No se pudo iniciar la operación.',
                }
              : t,
          ),
        )
        finishSlot()
      }
    },
    [finishSlot],
  )

  dispatchRef.current = dispatch

  useEffect(() => {
    return window.api.onOperationMessage(({ requestId, data }) => {
      const taskId = requestIdToTaskId.current.get(requestId)
      if (!taskId) {
        const buffered = pendingMessages.current.get(requestId) ?? []
        buffered.push(data)
        pendingMessages.current.set(requestId, buffered)
        return
      }

      setTasks((prev) => {
        const index = prev.findIndex((t) => t.id === taskId)
        if (index === -1) return prev
        const next = [...prev]
        next[index] = applyMessage(next[index], data)
        return next
      })

      if (data.type === 'result') {
        finishSlot()
      }
    })
  }, [finishSlot])

  const submit = useCallback(
    (name: string, operation: string, params: unknown) => {
      const id = crypto.randomUUID()
      const sub: QueuedSubmission = { id, name, operation, params }

      if (activeCount.current < MAX_CONCURRENT) {
        activeCount.current += 1
        setTasks((prev) => [{ id, name, status: 'running', progress: 0, output: null, error: null }, ...prev])
        dispatch(sub)
      } else {
        queue.current.push(sub)
        setTasks((prev) => [{ id, name, status: 'pending', progress: 0, output: null, error: null }, ...prev])
      }
    },
    [dispatch],
  )

  const cancel = useCallback((taskId: string) => {
    const queueIndex = queue.current.findIndex((s) => s.id === taskId)
    if (queueIndex !== -1) {
      // Aún no se había lanzado: se retira de la cola sin tocar el backend.
      queue.current.splice(queueIndex, 1)
      setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, status: 'cancelled', progress: 0 } : t)))
      return
    }
    const requestId = taskIdToRequestId.current.get(taskId)
    if (requestId) {
      window.api.cancelOperation(requestId)
    }
  }, [])

  return { tasks, submit, cancel }
}
