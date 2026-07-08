import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTaskQueue } from './useTaskQueue'
import type { OperationMessage } from '../../electron/preload'

type Listener = (message: { requestId: string; data: OperationMessage }) => void

interface StartedOp {
  operation: string
  params: unknown
  requestId: string
}

function createFakeApi({ startDelayMs = 0 }: { startDelayMs?: number } = {}) {
  let listener: Listener | null = null
  let counter = 0
  const startedOperations: StartedOp[] = []
  const cancelledRequestIds: string[] = []

  const startOperation = vi.fn((operation: string, params: unknown) => {
    const requestId = `req-${++counter}`
    startedOperations.push({ operation, params, requestId })
    if (startDelayMs > 0) {
      return new Promise<{ requestId: string }>((resolve) => setTimeout(() => resolve({ requestId }), startDelayMs))
    }
    return Promise.resolve({ requestId })
  })

  const cancelOperation = vi.fn((requestId: string) => {
    cancelledRequestIds.push(requestId)
    return Promise.resolve()
  })

  const onOperationMessage = vi.fn((cb: Listener) => {
    listener = cb
    return () => {
      listener = null
    }
  })

  return {
    api: { startOperation, cancelOperation, onOperationMessage },
    startedOperations,
    cancelledRequestIds,
    emit(requestId: string, data: OperationMessage) {
      listener?.({ requestId, data })
    },
  }
}

// Cada test se queda con la última fake api instalada en window.api.
function installFakeApi(fake: ReturnType<typeof createFakeApi>) {
  (window as unknown as { api: unknown }).api = fake.api
}

describe('useTaskQueue', () => {
  beforeEach(() => {
    let n = 0
    vi.stubGlobal('crypto', { randomUUID: () => `id-${++n}` })
  })

  it('runs up to MAX_CONCURRENT (2) immediately and queues the rest as pending', async () => {
    const fake = createFakeApi()
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
      result.current.submit('Task B', 'op_b', {})
      result.current.submit('Task C', 'op_c', {})
    })

    expect(result.current.tasks).toHaveLength(3)
    // submit prepends, así que el orden en tasks es [C, B, A]
    const byName = Object.fromEntries(result.current.tasks.map((t) => [t.name, t]))
    expect(byName['Task A'].status).toBe('running')
    expect(byName['Task B'].status).toBe('running')
    expect(byName['Task C'].status).toBe('pending')
    // Solo A y B deberían haber llegado de verdad al backend.
    expect(fake.startedOperations.map((o) => o.operation)).toEqual(['op_a', 'op_b'])
  })

  it('promotes the pending task once a running one finishes', async () => {
    const fake = createFakeApi()
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
      result.current.submit('Task B', 'op_b', {})
      result.current.submit('Task C', 'op_c', {})
    })

    const requestIdA = fake.startedOperations[0].requestId

    await act(async () => {
      fake.emit(requestIdA, { type: 'result', success: true, output: '/out/a.mp4' })
    })

    // C ha debido despacharse al backend al liberarse el hueco de A.
    expect(fake.startedOperations.map((o) => o.operation)).toEqual(['op_a', 'op_b', 'op_c'])

    const byName = Object.fromEntries(result.current.tasks.map((t) => [t.name, t]))
    expect(byName['Task A'].status).toBe('done')
    expect(byName['Task A'].output).toBe('/out/a.mp4')
    expect(byName['Task C'].status).toBe('running')
  })

  it('routes progress messages to the right task by requestId', async () => {
    const fake = createFakeApi()
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
    })
    const requestId = fake.startedOperations[0].requestId

    await act(async () => {
      fake.emit(requestId, { type: 'progress', percent: 42 })
    })

    expect(result.current.tasks[0].progress).toBe(42)
    expect(result.current.tasks[0].status).toBe('running')
  })

  it('cancelling a pending task removes it from the queue without calling the backend', async () => {
    const fake = createFakeApi()
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
      result.current.submit('Task B', 'op_b', {})
      result.current.submit('Task C', 'op_c', {})
    })

    const pending = result.current.tasks.find((t) => t.name === 'Task C')!

    act(() => {
      result.current.cancel(pending.id)
    })

    expect(result.current.tasks.find((t) => t.name === 'Task C')!.status).toBe('cancelled')
    expect(fake.cancelledRequestIds).toHaveLength(0)
    expect(fake.startedOperations).toHaveLength(2) // C nunca llegó a lanzarse
  })

  it('cancelling a running task calls cancelOperation with its requestId', async () => {
    const fake = createFakeApi()
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
    })
    const running = result.current.tasks[0]
    const requestId = fake.startedOperations[0].requestId

    act(() => {
      result.current.cancel(running.id)
    })

    expect(fake.cancelledRequestIds).toEqual([requestId])
  })

  it('buffers messages that arrive before startOperation resolves and applies them once it does', async () => {
    const fake = createFakeApi({ startDelayMs: 20 })
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    act(() => {
      result.current.submit('Task A', 'op_a', {})
    })

    // El requestId ya se conoce de forma síncrona (se genera antes de que
    // resuelva la promesa de startOperation), pero el hook aún no lo ha
    // registrado -> estos mensajes deben quedar en buffer, no perderse.
    const requestId = fake.startedOperations[0].requestId
    act(() => {
      fake.emit(requestId, { type: 'progress', percent: 55 })
      fake.emit(requestId, { type: 'result', success: true, output: '/out/a.mp4' })
    })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 40))
    })

    expect(result.current.tasks[0].status).toBe('done')
    expect(result.current.tasks[0].output).toBe('/out/a.mp4')
  })

  it('surfaces a startOperation rejection as an error task instead of an unhandled rejection', async () => {
    const fake = createFakeApi()
    fake.api.startOperation.mockRejectedValueOnce(new Error('boom'))
    installFakeApi(fake)
    const { result } = renderHook(() => useTaskQueue())

    await act(async () => {
      result.current.submit('Task A', 'op_a', {})
    })

    expect(result.current.tasks[0].status).toBe('error')
    expect(result.current.tasks[0].error).toBe('boom')
  })
})
