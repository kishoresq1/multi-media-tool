import { useEffect, useState } from 'react'
import { Plus, Tag } from 'lucide-react'
import { api, ApiError, type KeywordsResponse } from '../api/client'
import { ErrorBanner, Loading, PageHeader } from '../components/shared'

export function Keywords() {
  const [data, setData] = useState<KeywordsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [newKeyword, setNewKeyword] = useState('')
  const [targetCategory, setTargetCategory] = useState<'primary' | 'vendors' | 'vulnerability' | 'threat_activity'>('primary')

  useEffect(() => {
    api.keywords()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Failed'))
      .finally(() => setLoading(false))
  }, [])

  const handleAddKeyword = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyword.trim() || !data) return

    const keyword = newKeyword.trim()
    
    // UI-only update
    const updatedData = { ...data }
    if (targetCategory === 'primary') {
      updatedData.primary = [keyword, ...updatedData.primary]
    } else {
      updatedData.fallback[targetCategory] = [keyword, ...updatedData.fallback[targetCategory]]
    }
    
    setData(updatedData)
    setNewKeyword('')
    alert(`Keyword "${keyword}" added to ${targetCategory} (UI only)`)
  }

  if (loading) return <Loading />
  if (error) return <><PageHeader title="Keywords" /><ErrorBanner message={error} /></>
  if (!data) return null

  return (
    <>
      <PageHeader
        title="Search keywords"
        description="GET /keywords — primary SEARCH_KEYWORDS used first; vendor/vuln/activity as fallback"
      />

      <section className="config-section">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '1.25rem' }}>
          <Tag size={20} color="var(--accent)" />
          <h3>Add new keyword</h3>
        </div>
        <form onSubmit={handleAddKeyword} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '240px', marginBottom: 0 }}>
            <label>Keyword</label>
            <input
              type="text"
              placeholder="e.g. Zero-day, Ransomware..."
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              required
            />
          </div>
          <div className="form-group" style={{ width: '200px', marginBottom: 0 }}>
            <label>Category</label>
            <select
              value={targetCategory}
              onChange={(e) => setTargetCategory(e.target.value as any)}
            >
              <option value="primary">Primary (Search)</option>
              <option value="vendors">Fallback: Vendors</option>
              <option value="vulnerability">Fallback: Vulnerability</option>
              <option value="threat_activity">Fallback: Activity</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary" style={{ height: '42px' }}>
            <Plus size={16} /> Add Keyword
          </button>
        </form>
      </section>

      <section className="config-section">
        <h3>Priority</h3>
        <p style={{ color: 'var(--text-muted)' }}>{data.priority}</p>
      </section>

      <section className="config-section">
        <h3>Primary — SEARCH_KEYWORDS ({data.primary.length})</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {data.primary.map((k) => (
            <span key={k} className="badge badge-accent">{k}</span>
          ))}
        </div>
      </section>

      <div className="grid-2">
        <section className="config-section">
          <h3>Fallback vendors ({data.fallback.vendors.length})</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {data.fallback.vendors.map((k) => (
              <span key={k} className="badge badge-neutral">{k}</span>
            ))}
          </div>
        </section>
        <section className="config-section">
          <h3>Fallback vulnerability ({data.fallback.vulnerability.length})</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 200, overflow: 'auto' }}>
            {data.fallback.vulnerability.map((k) => (
              <span key={k} className="badge badge-neutral">{k}</span>
            ))}
          </div>
        </section>
      </div>

      <section className="config-section">
        <h3>Fallback activity keywords ({data.fallback.threat_activity.length})</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {data.fallback.threat_activity.map((k) => (
            <span key={k} className="badge badge-warning">{k}</span>
          ))}
        </div>
      </section>
    </>
  )
}
