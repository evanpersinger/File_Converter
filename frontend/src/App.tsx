import { useEffect, useState } from 'react'
import { convert, extensionOf, getFormats } from './api'
import type { FormatMap } from './types'
import './App.css'

type Status =
  | { kind: 'idle' }
  | { kind: 'converting' }
  | { kind: 'error'; message: string }

interface Result {
  url: string
  filename: string
}

export default function App() {
  const [formats, setFormats] = useState<FormatMap | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [target, setTarget] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [result, setResult] = useState<Result | null>(null)

  useEffect(() => {
    getFormats().then(setFormats).catch((e: Error) => setLoadError(e.message))
  }, [])

  // Release the blob URL when it gets replaced or the page unmounts. Without this,
  // every conversion would leak its result until a full page reload.
  useEffect(() => {
    if (!result) return
    return () => URL.revokeObjectURL(result.url)
  }, [result])

  const ext = file ? extensionOf(file.name) : ''
  const targets = (ext && formats?.byExtension[ext]) || []
  const blocked = (ext && formats?.unavailable[ext]) || []

  function pickFile(picked: File | null) {
    setFile(picked)
    setTarget(null)
    setStatus({ kind: 'idle' })
    setResult(null)
  }

  async function runConversion() {
    if (!file || !target) return
    setStatus({ kind: 'converting' })
    setResult(null)
    try {
      const { blob, filename } = await convert(file, target)
      // Hold the result and let the user click Download, rather than firing the
      // download automatically.
      setResult({ url: URL.createObjectURL(blob), filename })
      setStatus({ kind: 'idle' })
    } catch (e) {
      setStatus({ kind: 'error', message: (e as Error).message })
    }
  }

  return (
    <main>
      <h1>File Converter</h1>

      {loadError && <p className="error">{loadError}</p>}

      <label className="filepicker">
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

      {result && (
        <a className="download" href={result.url} download={result.filename}>
          Download {result.filename}
        </a>
      )}

      {status.kind === 'error' && <pre className="error">{status.message}</pre>}
    </main>
  )
}
