import type { ApiError, FormatMap } from './types'

export async function getFormats(): Promise<FormatMap> {
  const response = await fetch('/api/formats')
  if (!response.ok) {
    throw new Error('Could not reach the converter backend.')
  }
  return response.json()
}

export interface Converted {
  blob: Blob
  filename: string
}

export async function convert(file: File, targetId: string): Promise<Converted> {
  const body = new FormData()
  body.append('file', file)
  body.append('target', targetId)

  const response = await fetch('/api/convert', { method: 'POST', body })

  if (!response.ok) {
    // The backend always reports failures as {error, hint}.
    let message = `Conversion failed (${response.status}).`
    let hint: string | null | undefined
    try {
      const payload: ApiError = await response.json()
      message = payload.error ?? message
      hint = payload.hint
    } catch {
      // Non-JSON error body, keep the generic message.
    }
    throw new Error(hint ? `${message}\n\n${hint}` : message)
  }

  return {
    blob: await response.blob(),
    filename: filenameFrom(response.headers.get('Content-Disposition')),
  }
}

/** Pull the download name out of `attachment; filename="report.pdf"`. */
function filenameFrom(disposition: string | null): string {
  const match = disposition?.match(/filename="(.+?)"/)
  return match ? match[1] : 'converted'
}

/** Extension of a filename, lowercased and including the dot. "" if there is none. */
export function extensionOf(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot === -1 ? '' : filename.slice(dot).toLowerCase()
}
