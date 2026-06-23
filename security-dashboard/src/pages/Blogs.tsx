import { useCallback, useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { api, ApiError, type BlogPost } from '../api/client'
import { ErrorBanner, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, pct, scoreClass } from '../lib/format'

export function Blogs() {
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [lookback, setLookback] = useState(30)

  const load = useCallback(async () => {
    try {
      const res = await api.blogs({ min_score: 0, limit: 100 })
      setPosts(res.posts)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    try {
      const res = await api.blogSearch({ lookback_days: lookback, include_low_confidence: true })
      setSuccess(`Saved ${res.posts_saved} posts (${res.duration_seconds}s)`)
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
        title="Research blogs"
        description="POST /blogs/search · GET /blogs — Project Zero, Unit42, Krebs, DFIR, etc."
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section">
        <h3>Fetch blogs</h3>
        <div className="form-group">
          <label>Lookback days</label>
          <input type="number" value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
        </div>
        <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching}>
          <Play size={16} /> {searching ? 'Fetching…' : 'POST /blogs/search'}
        </button>
      </section>

      <span className="badge badge-neutral" style={{ marginBottom: '1rem', display: 'inline-block' }}>{total} posts</span>

      <section className="panel">
        <table className="data-table">
          <thead><tr><th>Source</th><th>Title</th><th>Keywords</th><th>Score</th><th>Date</th></tr></thead>
          <tbody>
            {posts.map((p) => (
              <tr key={p.id}>
                <td><span className="badge badge-neutral">{p.source_name}</span></td>
                <td className="title-cell">
                  {p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title}</a> : p.title}
                </td>
                <td>{p.matched_vuln_keywords.slice(0, 2).join(', ') || '—'}</td>
                <td className={`score ${scoreClass(p.confidence_score)}`}>{pct(p.confidence_score)}</td>
                <td>{formatDate(p.published_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}
