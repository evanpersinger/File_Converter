import { useEffect, useState } from 'react'
import { convert, extensionOf, getFormats } from './api'
import type { FormatMap } from './types'
import './App.css'

type Status =
  | { kind: 'idle' }
  | { kind: 'converting' }
  | { kind: 'done'; filename: string }
  | { kind: 'error'; message: string }

export default function App() {
  const [formats, setFormats] = useState<FormatMap | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [target, setTarget] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })

  useEffect(() => {
    getFormats().then(setFormats).catch((e: Error) => setLoadError(e.message))
  }, [])

  const ext = file ? extensionOf(file.name) : ''
  const targets = (ext && formats?.byExtension[ext]) || []
  const blocked = (ext && formats?.unavailable[ext]) || []

  function pickFile(picked: File | null) {
    setFile(picked)
    setTarget(null)
    setStatus({ kind: 'idle' })
  }

  async function runConversion() {
    if (!file || !target) return
    setStatus({ kind: 'converting' })
    try {
      const { blob, filename } = await convert(file, target)
      // Hand the bytes straight to the browser as a download.
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
      setStatus({ kind: 'done', filename })
    } catch (e) {
      setStatus({ kind: 'error', message: (e as Error).message })
    }
  }

  return (
    <main>
      <h1>File Converter</h1>

      {loadError && <p className="error">{loadError}</p>}

      <label className="dropzone">
        <input type="file" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
        <span>{file ? file.name : 'Choose a file'}</span>
      </label>

      {file && (
        <section>
          <h2>Convert to</h2>

          {targets.length === 0 && blocked.length === 0 && (
            <p className="muted">No conversions available for {ext || 'this file'}.</p>
          )}

          {targets.map((t) => (
            <label key={t.id} className="option">
              <input
                type="radio"
                name="target"
                value={t.id}
                checked={target === t.id}
                onChange={() => setTarget(t.id)}
              />
              <span>
                {t.label} <code>{t.ext}</code>
                {t.note && <em className="note">{t.note}</em>}
              </span>
            </label>
          ))}

          {blocked.map((u) => (
            <div key={u.id} className="option disabled">
              <input type="radio" disabled />
              <span>
                {u.label}
                <em className="note">
                  {u.reason}
                  {u.hint && (
                    <>
                      {' · '}
                      <code>{u.hint}</code>
                    </>
                  )}
                </em>
              </span>
            </div>
          ))}

          <button onClick={runConversion} disabled={!target || status.kind === 'converting'}>
            {status.kind === 'converting' ? 'Converting...' : 'Convert'}
          </button>
        </section>
      )}

      {status.kind === 'done' && <p className="success">Downloaded {status.filename}</p>}
      {status.kind === 'error' && <pre className="error">{status.message}</pre>}
    </main>
  )
}
