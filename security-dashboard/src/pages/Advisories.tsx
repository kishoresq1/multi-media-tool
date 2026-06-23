import { useCallback, useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { api, ApiError, type Advisory } from '../api/client'
import { ErrorBanner, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, pct, scoreClass } from '../lib/format'

export function Advisories() {
  const [items, setItems] = useState<Advisory[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<Advisory | null>(null)
  const [vendor, setVendor] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [lookback, setLookback] = useState(30)

  const load = useCallback(async () => {
    setError(null)
    try {
      const res = await api.advisories({ vendor: vendor || undefined, min_score: minScore, limit: 100 })
      setItems(res.advisories)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [vendor, minScore])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    setError(null)
    try {
      const res = await api.advisorySearch({
        lookback_days: lookback,
        min_confidence: minScore,
        include_low_confidence: true,
      })
      setSuccess(`Saved ${res.advisories_saved} advisories in ${res.duration_seconds}s`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  if (loading) return <Loading />

  return (
    <>
      <PageHeader
        title="Vendor advisories"
        description="POST /advisories/search · GET /advisories — MSRC, Cisco, Fortinet, Chrome, etc."
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section">
        <h3>Fetch advisories</h3>
        <div className="form-row">
          <div className="form-group">
            <label>Lookback days</label>
            <input type="number" value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Min confidence</label>
            <input type="number" min={0} max={1} step={0.1} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
          </div>
        </div>
        <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching}>
          <Play size={16} /> {searching ? 'Fetching…' : 'POST /advisories/search'}
        </button>
      </section>

      <div className="filter-bar">
        <input placeholder="Filter vendor…" value={vendor} onChange={(e) => setVendor(e.target.value)} />
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header"><h3>Advisories</h3></div>
          <table className="data-table">
            <thead><tr><th>Vendor</th><th>Title</th><th>Score</th><th>Date</th></tr></thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id} onClick={() => setSelected(a)} style={{ cursor: 'pointer' }}>
                  <td>{a.vendor || '—'}</td>
                  <td className="title-cell">{a.title.slice(0, 70)}</td>
                  <td className={`score ${scoreClass(a.confidence_score)}`}>{pct(a.confidence_score)}</td>
                  <td>{formatDate(a.published_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="panel">
          <div className="panel-header"><h3>Detail</h3></div>
          <div style={{ padding: '1.25rem' }}>
            {selected ? (
              <>
                <h4>{selected.title}</h4>
                <p style={{ fontSize: '0.85rem', margin: '12px 0', color: 'var(--text-muted)' }}>{selected.content.slice(0, 600)}</p>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {selected.severity && <span className="badge badge-danger">{selected.severity}</span>}
                  {selected.cves.map((c) => <span key={c} className="badge badge-warning">{c}</span>)}
                </div>
                {selected.url && <p style={{ marginTop: 12 }}><a href={selected.url} target="_blank" rel="noreferrer">Open advisory</a></p>}
              </>
            ) : <p className="empty-state">Select a row</p>}
          </div>
        </section>
      </div>
    </>
  )
}
