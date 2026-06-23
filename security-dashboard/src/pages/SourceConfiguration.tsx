import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import { api, type SourceInfo } from '../api/client'

const STORAGE_KEY = 'zdr_source_config'

interface SourceOverride {
  enabled: boolean
  trust_weight: number
}

export function SourceConfiguration() {
  const [sources, setSources] = useState<SourceInfo[]>([])
  const [overrides, setOverrides] = useState<Record<string, SourceOverride>>({})
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)
  const [lookback, setLookback] = useState(30)
  const [minConfidence, setMinConfidence] = useState(0.3)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        setOverrides(JSON.parse(stored))
      } catch {
        /* ignore */
      }
    }
    api.sources().then((list) => {
      setSources(list)
      setLoading(false)
    })
  }, [])

  const toggle = (id: string, enabled: boolean) => {
    setOverrides((prev) => ({
      ...prev,
      [id]: { ...prev[id], enabled, trust_weight: prev[id]?.trust_weight ?? 0.5 },
    }))
    setSaved(false)
  }

  const setTrust = (id: string, trust_weight: number) => {
    setOverrides((prev) => ({
      ...prev,
      [id]: { enabled: prev[id]?.enabled ?? true, trust_weight },
    }))
    setSaved(false)
  }

  const save = () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ overrides, lookback, minConfidence }),
    )
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) return <div className="loading">Loading configuration…</div>

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Source configuration</h2>
          <p>Toggle collectors, adjust trust weights, and set global hunt parameters. Saved locally until backend persistence is added.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={save}>
          <Save size={16} />
          {saved ? 'Saved' : 'Save changes'}
        </button>
      </div>

      <section className="config-section">
        <h3>Global hunt settings</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="lookback">Lookback (days)</label>
            <input
              id="lookback"
              type="number"
              min={1}
              max={365}
              value={lookback}
              onChange={(e) => setLookback(Number(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confidence">Min confidence (0–1)</label>
            <input
              id="confidence"
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Per-source overrides ({sources.length})</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Category</th>
              <th>Enabled</th>
              <th>Trust weight</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => {
              const o = overrides[s.id]
              const enabled = o?.enabled ?? s.enabled
              const trust = o?.trust_weight ?? s.trust_weight
              return (
                <tr key={s.id}>
                  <td>
                    <strong>{s.name}</strong>
                    <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.id}</div>
                  </td>
                  <td><span className="badge badge-neutral">{s.category}</span></td>
                  <td>
                    <button
                      type="button"
                      className={`toggle${enabled ? ' on' : ''}`}
                      onClick={() => toggle(s.id, !enabled)}
                      aria-label={`Toggle ${s.name}`}
                    />
                  </td>
                  <td>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={trust}
                      onChange={(e) => setTrust(s.id, Number(e.target.value))}
                      style={{ width: 120 }}
                    />
                    <span className="mono" style={{ marginLeft: 8 }}>{(trust * 100).toFixed(0)}%</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>
    </>
  )
}
