// Electron eliminó `File.path` (deprecado desde la v32); la sustitución oficial
// es `webUtils.getPathForFile`, expuesta vía contextBridge en preload.ts.
export function getDroppedPaths(dataTransfer: DataTransfer): string[] {
  return Array.from(dataTransfer.files)
    .map((file) => window.api.getPathForFile(file))
    .filter((path): path is string => Boolean(path))
}

export function extensionOf(path: string): string {
  return path.split('.').pop()?.toLowerCase() ?? ''
}

export function baseName(path: string): string {
  return path.replace(/[\\/]+$/, '').split(/[\\/]/).pop() ?? path
}
