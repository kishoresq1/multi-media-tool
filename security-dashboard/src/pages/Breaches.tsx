import { useCallback, useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { api, ApiError, type BreachIntel } from '../api/client'
import { DetailGrid, ErrorBanner, KeywordTags, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, saintScore, saintScoreClass } from '../lib/format'

const SOURCES = [
  '',
  'krebsonsecurity',
  'bleepingcomputer',
  'securityweek',
  'the_hacker_news',
  'ransomware_live',
]

export function Breaches() {
  const [items, setItems] = useState<BreachIntel[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<BreachIntel | null>(null)
  const [sourceId, setSourceId] = useState('')
  const [lookback, setLookback] = useState(30)

  const load = useCallback(async () => {
    setError(null)
    try {
      const res = await api.breaches({ source_id: sourceId || undefined, min_score: 0, limit: 100 })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [sourceId])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    setError(null)
    try {
      const res = await api.breachSearch({
        lookback_days: lookback,
        min_confidence: 20,
        include_low_confidence: true,
      })
      setSuccess(`Saved ${res.items_saved} breach records in ${res.duration_seconds}s`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  if (loading) return <Loading text="Loading breach intel…" />

  return (
    <>
      <PageHeader
        title="Company breaches"
        description="Tier 1 — KrebsOnSecurity · BleepingComputer · SecurityWeek · The Hacker News · Ransomware.live"
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section">
        <h3>Fetch breach news (last 30 days)</h3>
        <div className="form-group">
          <label>Lookback days</label>
          <input type="number" value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
        </div>
        <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching}>
          <Play size={16} /> {searching ? 'Fetching…' : 'POST /breaches/search'}
        </button>
      </section>

      <div className="filter-bar">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          {SOURCES.map((s) => (
            <option key={s || 'all'} value={s}>{s || 'All sources'}</option>
          ))}
        </select>
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header"><h3>Breach incidents</h3></div>
          <table className="data-table">
            <thead>
              <tr><th>Source</th><th>Company</th><th>Title</th><th>Type</th><th>Risk</th><th>Score</th><th>Date</th></tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} onClick={() => setSelected(row)} style={{ cursor: 'pointer' }}>
                  <td>{row.source_name}</td>
                  <td style={{ fontSize: '0.8rem' }}>{row.affected_company || '—'}</td>
                  <td className="title-cell">{row.title.slice(0, 55)}</td>
                  <td>
                    {row.is_ransomware && <span className="badge badge-danger">ransomware</span>}
                    {row.breach_type && !row.is_ransomware && (
                      <span className="badge badge-warning">{row.breach_type}</span>
                    )}
                  </td>
                  <td><span className="badge badge-neutral">{row.risk_level}</span></td>
                  <td className={`score ${saintScoreClass(row.confidence_score)}`}>{saintScore(row.confidence_score)}</td>
                  <td>{formatDate(row.published_at)}</td>
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
                <DetailGrid
                  rows={[
                    { label: 'Affected company', value: selected.affected_company },
                    { label: 'Breach type', value: selected.breach_type },
                    { label: 'Source tier', value: selected.source_tier },
                    { label: 'Risk level', value: selected.risk_level },
                    { label: 'Confidence', value: `${saintScore(selected.confidence_score)} / 100` },
                    { label: 'Trust / keyword / recency', value: `${selected.source_trust_score.toFixed(0)} · ${selected.keyword_match_score.toFixed(0)} · ${selected.recency_score.toFixed(0)}` },
                    { label: 'Ransomware', value: selected.is_ransomware ? 'Yes' : 'No' },
                    { label: 'Active exploitation', value: selected.active_exploitation ? 'Yes' : 'No' },
                    { label: 'Has PoC', value: selected.has_poc ? 'Yes' : 'No' },
                    { label: 'Author', value: selected.author },
                    { label: 'Published', value: formatDate(selected.published_at) },
                    { label: 'Score reason', value: selected.score_reason || '—' },
                  ]}
                />
                <KeywordTags items={selected.matched_breach_keywords} />
                {selected.matched_vendors.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Vendors</strong>
                    <KeywordTags items={selected.matched_vendors} />
                  </div>
                )}
                {selected.cves.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>CVEs</strong>
                    <KeywordTags items={selected.cves} />
                  </div>
                )}
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 12 }}>
                  {selected.content.slice(0, 600)}
                </p>
                {selected.url && (
                  <p><a href={selected.url} target="_blank" rel="noreferrer">Open article</a></p>
                )}
              </>
            ) : (
              <p className="empty-state">Select a row</p>
            )}
          </div>
        </section>
      </div>
    </>
  )
}
