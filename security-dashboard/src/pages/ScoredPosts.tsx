import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api, ApiError, type ScoredPost } from '../api/client'
import { ErrorBanner, Loading, PageHeader } from '../components/shared'
import { formatDate, pct, scoreClass } from '../lib/format'

export function ScoredPosts() {
  const [posts, setPosts] = useState<ScoredPost[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [minConf, setMinConf] = useState(0.3)

  const load = async () => {
    setError(null)
    try {
      const res = await api.scoredPosts({ min_confidence: minConf, limit: 50 })
      setPosts(res.posts)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [minConf])

  if (loading) return <Loading />

  return (
    <>
      <PageHeader
        title="Scored posts"
        description="GET /posts — correlated & scored findings from pipeline runs"
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}

      <div className="filter-bar">
        <label>Min confidence <input type="number" min={0} max={1} step={0.1} value={minConf} onChange={(e) => setMinConf(Number(e.target.value))} style={{ width: 70, marginLeft: 8 }} /></label>
        <span className="badge badge-neutral">{total} posts</span>
      </div>

      <section className="panel">
        <table className="data-table">
          <thead>
            <tr><th>Title</th><th>Vendors</th><th>CVEs</th><th>Flags</th><th>Score</th><th>Date</th></tr>
          </thead>
          <tbody>
            {posts.map((p) => (
              <tr key={p.id}>
                <td className="title-cell">
                  {p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title}</a> : p.title}
                </td>
                <td>{p.vendors.slice(0, 2).join(', ') || '—'}</td>
                <td className="mono">{p.cves.slice(0, 2).join(', ') || '—'}</td>
                <td>
                  {p.in_cisa_kev && <span className="badge badge-danger">KEV</span>}
                  {p.has_poc && <span className="badge badge-warning">PoC</span>}
                </td>
                <td className={`score ${scoreClass(p.confidence_score)}`}>{pct(p.confidence_score)}</td>
                <td>{formatDate(p.published_at)}</td>
              </tr>
            ))}
            {!posts.length && <tr><td colSpan={6} className="empty-state">No scored posts — run pipeline first</td></tr>}
          </tbody>
        </table>
      </section>
    </>
  )
}
