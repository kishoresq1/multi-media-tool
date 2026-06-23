import { useEffect, useMemo, useState } from 'react'
import { ExternalLink, Edit2, Plus, Search, X } from 'lucide-react'
import { api, API_BASE, ApiError, type SourceInfo } from '../api/client'

const CATEGORY_LABELS: Record<string, string> = {
  researcher_social: 'Social',
  researcher_blog: 'Blogs',
  vendor_advisory: 'Advisories',
  vulnerability: 'Vulnerability',
  company_breach_intel: 'Company breaches',
  compliance: 'Compliance',
  conference: 'Conference',
  dark_web_intel: 'Dark web',
}

export function SourcesList() {
  const [sources, setSources] = useState<SourceInfo[]>([])
  const [enabledStates, setEnabledStates] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<SourceInfo | null>(null)

  // Form state for new source
  const [newSource, setNewSource] = useState({
    name: '',
    url: '',
    category: 'researcher_blog',
    scraping_type: 'web_scrape',
    auth_type: 'authless',
    trust_weight: 0.8,
  })

  useEffect(() => {
    api.sources()
      .then((data) => {
        setSources(data)
        const initialStates: Record<string, boolean> = {}
        data.forEach((s) => {
          initialStates[s.id] = s.enabled
        })
        setEnabledStates(initialStates)
      })
      .catch((e) => {
        const msg = e instanceof ApiError ? e.message : String(e)
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [])

  const categories = useMemo(() => {
    const set = new Set(sources.map((s) => s.category))
    return ['all', ...Array.from(set).sort()]
  }, [sources])

  const filtered = useMemo(() => {
    return sources.filter((s) => {
      const matchCat = category === 'all' || s.category === category
      const q = search.toLowerCase()
      const matchSearch =
        !q ||
        s.name.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q)
      return matchCat && matchSearch
    })
  }, [sources, search, category])

  const handleAddSource = (e: React.FormEvent) => {
    e.preventDefault()
    // User requested "no need to integrate", so we just close the modal
    // In a real app, we would call an API here.
    setIsModalOpen(false)
    setEditingSource(null)
    alert(editingSource ? 'Source updated (UI only)' : 'Source configuration saved (UI only)')
  }

  const openEditModal = (s: SourceInfo) => {
    setEditingSource(s)
    setNewSource({
      name: s.name,
      url: s.url,
      category: s.category,
      scraping_type: s.primary_method,
      auth_type: s.requires_api_key ? 'api_key' : 'authless',
      trust_weight: s.trust_weight,
    })
    setIsModalOpen(true)
  }

  const toggleSource = (id: string) => {
    setEnabledStates((prev) => ({
      ...prev,
      [id]: !prev[id],
    }))
  }

  if (loading) return <div className="loading">Loading sources…</div>

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Sources list</h2>
          <p>All configured data sources — RSS, API, scraper, and GitHub collectors wired to the backend pipeline.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => { setEditingSource(null); setIsModalOpen(true); }}>
          <Plus size={16} /> Add Source
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <div style={{ marginTop: 6, fontSize: '0.8rem' }}>API base: <code>{API_BASE}</code></div>
        </div>
      )}

      <div className="filter-bar">
        <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
          <Search size={16} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="search"
            placeholder="Search sources…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 34, width: '100%' }}
          />
        </div>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === 'all' ? 'All categories' : CATEGORY_LABELS[c] ?? c}
            </option>
          ))}
        </select>
        <span className="badge badge-neutral">{filtered.length} sources</span>
      </div>

      <div className="source-grid">
        {filtered.map((s) => {
          const isEnabled = enabledStates[s.id] ?? s.enabled
          return (
            <article key={s.id} className="source-card" style={{ opacity: isEnabled ? 1 : 0.6 }}>
              <div className="source-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h4 style={{ color: isEnabled ? 'inherit' : 'var(--text-muted)' }}>{s.name}</h4>
                  <button 
                    type="button" 
                    className="btn btn-ghost" 
                    style={{ padding: 4, color: 'var(--text-muted)' }}
                    onClick={() => openEditModal(s)}
                    title="Edit source"
                  >
                    <Edit2 size={14} />
                  </button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`badge ${isEnabled ? 'badge-success' : 'badge-neutral'}`} style={{ fontSize: '0.65rem' }}>
                    {isEnabled ? 'Active' : 'Inactive'}
                  </span>
                  <div
                    className={`toggle ${isEnabled ? 'on' : ''}`}
                    onClick={() => toggleSource(s.id)}
                    title={isEnabled ? 'Disable source' : 'Enable source'}
                  />
                </div>
              </div>
              <p>{s.id}</p>
              <div className="source-card-meta">
                <span className="badge badge-accent">{CATEGORY_LABELS[s.category] ?? s.category}</span>
                <span className="badge badge-neutral">{s.primary_method}</span>
                {s.requires_api_key && <span className="badge badge-warning">API key</span>}
                <span className="badge badge-neutral">Trust {(s.trust_weight * 100).toFixed(0)}%</span>
              </div>
              <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', marginTop: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                Open source <ExternalLink size={12} />
              </a>
            </article>
          )
        })}
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: '500px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3>{editingSource ? 'Edit data source' : 'Add new data source'}</h3>
              <button type="button" className="btn btn-ghost" onClick={() => setIsModalOpen(false)} style={{ padding: 4 }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddSource}>
              <div className="form-group">
                <label>Source Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Microsoft Security Blog"
                  value={newSource.name}
                  onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Source URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://..."
                  value={newSource.url}
                  onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Category</label>
                  <select
                    value={newSource.category}
                    onChange={(e) => setNewSource({ ...newSource, category: e.target.value })}
                  >
                    {Object.entries(CATEGORY_LABELS).map(([val, label]) => (
                      <option key={val} value={val}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Trust Weight</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={newSource.trust_weight}
                    onChange={(e) => setNewSource({ ...newSource, trust_weight: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Scraping Type</label>
                  <select
                    value={newSource.scraping_type}
                    onChange={(e) => setNewSource({ ...newSource, scraping_type: e.target.value })}
                  >
                    <option value="web_scrape">Web Scrape (HTML)</option>
                    <option value="api">API Based</option>
                    <option value="rss">RSS Feed</option>
                    <option value="github">GitHub API</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Authentication</label>
                  <select
                    value={newSource.auth_type}
                    onChange={(e) => setNewSource({ ...newSource, auth_type: e.target.value })}
                  >
                    <option value="authless">Authless (Public)</option>
                    <option value="api_key">API Key / Token</option>
                    <option value="oauth">OAuth 2.0</option>
                    <option value="basic">Basic Auth</option>
                  </select>
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: '2rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingSource ? 'Update Source' : 'Save Source'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
