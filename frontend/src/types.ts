/** A conversion the backend can actually perform right now. */
export interface Target {
  id: string
  label: string
  ext: string
  note?: string
}

/** A conversion the backend knows about but cannot run, and why. */
export interface Unavailable {
  id: string
  label: string
  reason: string
  hint?: string
}

/**
 * The whole format map, keyed by lowercased source extension (".csv", ".pdf").
 * The frontend hardcodes no extensions and no format names, it only indexes this
 * by the uploaded file's extension. Adding a converter is a backend-only change.
 */
export interface FormatMap {
  byExtension: Record<string, Target[]>
  unavailable: Record<string, Unavailable[]>
}

export interface ApiError {
  error: string
  hint?: string | null
}
