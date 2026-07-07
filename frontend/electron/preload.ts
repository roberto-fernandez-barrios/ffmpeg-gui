import { ipcRenderer, contextBridge, type OpenDialogOptions } from 'electron'

export type OperationMessage =
  | { type: 'progress'; percent: number }
  | { type: 'pair_progress'; percent: number; pairIndex: number; pairsTotal: number; label: string }
  | {
      type: 'pair_done'
      pairIndex: number
      pairsTotal: number
      success: boolean
      output: string | null
      error: string | null
      label: string
    }
  | {
      type: 'result'
      success: boolean
      output?: string | null
      error?: string | null
      cancelled?: boolean
      pairs?: Array<{ label: string; success: boolean; output: string | null; error: string | null }>
    }

export interface FilePickerOptions {
  filters?: OpenDialogOptions['filters']
}

const api = {
  startOperation(operation: string, params: unknown): Promise<{ requestId: string }> {
    return ipcRenderer.invoke('operation:start', { operation, params })
  },
  cancelOperation(requestId: string): Promise<void> {
    return ipcRenderer.invoke('operation:cancel', { requestId })
  },
  onOperationMessage(callback: (message: { requestId: string; data: OperationMessage }) => void) {
    const listener = (_event: Electron.IpcRendererEvent, message: { requestId: string; data: OperationMessage }) =>
      callback(message)
    ipcRenderer.on('operation:message', listener)
    return () => {
      ipcRenderer.removeListener('operation:message', listener)
    }
  },
  pickFile(options?: FilePickerOptions): Promise<string | null> {
    return ipcRenderer.invoke('dialog:openFile', { ...options, multi: false })
  },
  pickFiles(options?: FilePickerOptions): Promise<string[]> {
    return ipcRenderer.invoke('dialog:openFile', { ...options, multi: true })
  },
  pickFolder(): Promise<string | null> {
    return ipcRenderer.invoke('dialog:openFolder')
  },
  openPath(path: string): Promise<string> {
    return ipcRenderer.invoke('shell:openPath', path)
  },
  openExternal(url: string): Promise<void> {
    return ipcRenderer.invoke('shell:openExternal', url)
  },
  checkDependencies(): Promise<{ ffmpeg: boolean; ffprobe: boolean }> {
    return ipcRenderer.invoke('dependencies:check')
  },
}

export type Api = typeof api

contextBridge.exposeInMainWorld('api', api)
