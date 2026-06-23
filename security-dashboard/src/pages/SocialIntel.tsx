import { useCallback, useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { api, ApiError, type IntelPost } from '../api/client'
import { ErrorBanner, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, pct, scoreClass } from '../lib/format'

export function SocialIntel() {
  const [posts, setPosts] = useState<IntelPost[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<IntelPost | null>(null)
  const [platform, setPlatform] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [lookback, setLookback] = useState(30)
  const [vendors, setVendors] = useState('')

  const load = useCallback(async () => {
    setError(null)
    try {
      const res = await api.socialPosts({
        platform: platform || undefined,
        min_score: minScore,
        limit: 100,
      })
      setPosts(res.posts)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [platform, minScore])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    setError(null)
    setSuccess(null)
    try {
      const vendorList = vendors ? vendors.split(',').map((v) => v.trim()).filter(Boolean) : undefined
      const res = await api.socialSearch({
        vendors: vendorList,
        lookback_days: lookback,
        min_confidence: minScore,
        include_low_confidence: minScore < 0.3,
        sources: ['twitter', 'reddit', 'hackernews', 'linkedin'],
      })
      setSuccess(`Saved ${res.posts_saved} posts in ${res.duration_seconds}s`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  if (loading) return <Loading text="Loading social posts…" />

  return (
    <>
      <PageHeader
        title="Social feeds"
        description="POST /social/search · GET /social/posts — Twitter, Reddit, HackerNews, LinkedIn"
        actions={
          <button type="button" className="btn btn-secondary" onClick={load}>
            <RefreshCw size={16} /> Refresh
          </button>
        }
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section">
        <h3>Run search</h3>
        <div className="form-row">
          <div className="form-group">
            <label>Vendors (comma-separated)</label>
            <input placeholder="Fortinet, Cisco, Microsoft" value={vendors} onChange={(e) => setVendors(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Lookback days</label>
            <input type="number" min={1} max={365} value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
          </div>
        </div>
        <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching}>
          <Play size={16} /> {searching ? 'Searching…' : 'POST /social/search'}
        </button>
      </section>

      <div className="filter-bar">
        <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
          <option value="">All platforms</option>
          <option value="twitter">Twitter</option>
          <option value="reddit">Reddit</option>
          <option value="hackernews">Hacker News</option>
          <option value="linkedin">LinkedIn</option>
        </select>
        <label>
          Min score{' '}
          <input type="number" min={0} max={1} step={0.1} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} style={{ width: 70 }} />
        </label>
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header"><h3>Posts</h3></div>
          <div className="panel-body">
            <table className="data-table">
              <thead>
                <tr><th>Platform</th><th>Title</th><th>Score</th><th>Date</th></tr>
              </thead>
              <tbody>
                {posts.map((p) => (
                  <tr key={p.id} onClick={() => setSelected(p)} style={{ cursor: 'pointer' }}>
                    <td><span className="badge badge-neutral">{p.platform}</span></td>
                    <td className="title-cell">{p.title.slice(0, 80)}</td>
                    <td className={`score ${scoreClass(p.confidence_score)}`}>{pct(p.confidence_score)}</td>
                    <td>{formatDate(p.published_at)}</td>
                  </tr>
                ))}
                {!posts.length && <tr><td colSpan={4} className="empty-state">No posts</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header"><h3>Detail · GET /social/posts/:id</h3></div>
          <div className="panel-body" style={{ padding: '1.25rem' }}>
            {selected ? (
              <>
                <h4 style={{ marginBottom: 8 }}>{selected.title}</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 12 }}>{selected.content.slice(0, 500)}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                  {selected.matched_vuln_keywords.map((k) => <span key={k} className="badge badge-accent">{k}</span>)}
                  {selected.cves.map((c) => <span key={c} className="badge badge-warning">{c}</span>)}
                </div>
                {selected.url && <a href={selected.url} target="_blank" rel="noreferrer">Open source →</a>}
              </>
            ) : (
              <p className="empty-state">Select a row to view details</p>
            )}
          </div>
        </section>
      </div>
    </>
  )
}
