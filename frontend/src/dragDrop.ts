// Electron añade `path` a los File nativos que llegan por drag & drop desde el
// explorador del sistema operativo, algo que la lib.dom.d.ts no declara.
interface FileWithPath extends File {
  path: string
}

export function getDroppedPaths(dataTransfer: DataTransfer): string[] {
  return Array.from(dataTransfer.files)
    .map((file) => (file as FileWithPath).path)
    .filter((path): path is string => Boolean(path))
}

export function extensionOf(path: string): string {
  return path.split('.').pop()?.toLowerCase() ?? ''
}
