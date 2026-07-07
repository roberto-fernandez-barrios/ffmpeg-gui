export type TaskStatus = 'pending' | 'running' | 'done' | 'error' | 'cancelled'

export interface Task {
  id: string
  name: string
  status: TaskStatus
  progress: number
  output: string | null
  error: string | null
}
