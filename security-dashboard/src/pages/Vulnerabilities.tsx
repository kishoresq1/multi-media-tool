import { useCallback, useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { api, ApiError, type VulnIntel } from '../api/client'
import { ErrorBanner, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, pct, scoreClass } from '../lib/format'

const SOURCES = ['', 'nvd', 'cisa_kev', 'cve_program', 'github_poc', 'exploit_db', 'metasploit']

export function Vulnerabilities() {
  const [items, setItems] = useState<VulnIntel[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<VulnIntel | null>(null)
  const [sourceId, setSourceId] = useState('')
  const [cveFilter, setCveFilter] = useState('')
  const [lookback, setLookback] = useState(30)

  const load = useCallback(async () => {
    try {
      const res = await api.vulnerabilities({
        source_id: sourceId || undefined,
        cve_id: cveFilter || undefined,
        min_score: 0,
        limit: 100,
      })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }, [sourceId, cveFilter])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    try {
      const res = await api.vulnerabilitySearch({ lookback_days: lookback, include_low_confidence: true })
      setSuccess(`Saved ${res.items_saved} records (${res.duration_seconds}s)`)
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
        title="Vulnerabilities"
        description="CVE Program · NVD · CISA KEV · GitHub · Exploit-DB · Metasploit"
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section">
        <h3>Fetch vulnerability data</h3>
        <div className="form-group">
          <label>Lookback days</label>
          <input type="number" value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
        </div>
        <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching}>
          <Play size={16} /> {searching ? 'Fetching…' : 'POST /vulnerabilities/search'}
        </button>
      </section>

      <div className="filter-bar">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          {SOURCES.map((s) => <option key={s} value={s}>{s || 'All sources'}</option>)}
        </select>
        <input placeholder="CVE-2024-1234" value={cveFilter} onChange={(e) => setCveFilter(e.target.value)} />
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <section className="panel">
        <table className="data-table">
          <thead>
            <tr><th>CVE</th><th>Source</th><th>Title</th><th>KEV</th><th>Score</th><th>Date</th></tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} onClick={() => setSelected(v)} style={{ cursor: 'pointer' }}>
                <td className="mono">{v.cve_id || '—'}</td>
                <td>{v.source_name}</td>
                <td className="title-cell">{v.title.slice(0, 55)}…</td>
                <td>{v.in_cisa_kev ? <span className="badge badge-danger">KEV</span> : '—'}</td>
                <td className={`score ${scoreClass(v.confidence_score)}`}>{pct(v.confidence_score)}</td>
                <td>{formatDate(v.published_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {selected && (
        <section className="config-section" style={{ marginTop: '1rem' }}>
          <h3>{selected.cve_id || selected.title}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{selected.content.slice(0, 800)}</p>
          {selected.url && <a href={selected.url} target="_blank" rel="noreferrer">View record →</a>}
        </section>
      )}
    </>
  )
}
