import { useCallback, useEffect, useState } from 'react'
import { Edit2, Play, RefreshCw, Scale } from 'lucide-react'
import {
  api,
  ApiError,
  type ComplianceIntel,
  type ComplianceKeywordsResponse,
  type ComplianceSource,
} from '../api/client'
import { DetailGrid, ErrorBanner, KeywordTags, Loading, PageHeader, SuccessBanner } from '../components/shared'
import { formatDate, saintScore, saintScoreClass } from '../lib/format'

export function Compliance() {
  const [items, setItems] = useState<ComplianceIntel[]>([])
  const [total, setTotal] = useState(0)
  const [sources, setSources] = useState<ComplianceSource[]>([])
  const [keywords, setKeywords] = useState<ComplianceKeywordsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<ComplianceIntel | null>(null)
  const [sourceId, setSourceId] = useState('')
  const [sourceTier, setSourceTier] = useState('')
  const [framework, setFramework] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [lookback, setLookback] = useState(30)

  const load = useCallback(async () => {
    setError(null)
    try {
      const res = await api.compliance({
        source_id: sourceId || undefined,
        framework: framework || undefined,
        source_tier: sourceTier ? Number(sourceTier) : undefined,
        min_score: minScore,
        limit: 100,
      })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [sourceId, sourceTier, framework, minScore])

  useEffect(() => {
    Promise.all([
      api.complianceSources().then((r) => setSources(r.sources)),
      api.complianceKeywords().then(setKeywords).catch(() => null),
    ]).catch(() => null)
  }, [])

  useEffect(() => { load() }, [load])

  const runSearch = async () => {
    setSearching(true)
    setError(null)
    try {
      const res = await api.complianceSearch({
        lookback_days: lookback,
        source_ids: sourceId ? [sourceId] : undefined,
        source_tier: sourceTier ? Number(sourceTier) : undefined,
        frameworks: framework ? [framework] : undefined,
        min_confidence: minScore,
        include_low_confidence: true,
      })
      setSuccess(`Saved ${res.items_saved} compliance records in ${res.duration_seconds.toFixed(1)}s`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  const tier1 = sources.filter((s) => s.tier === 1)
  const tier2 = sources.filter((s) => s.tier === 2)

  if (loading) return <Loading text="Loading compliance intel…" />

  return (
    <>
      <PageHeader
        title="Compliance intelligence"
        description="Regulatory updates, standards bodies, privacy authorities, and vendor compliance portals — NIST, ISO, PCI SSC, GDPR, EU AI Act, and more."
        actions={
          <button type="button" className="btn btn-secondary" onClick={load}>
            <RefreshCw size={16} /> Refresh
          </button>
        }
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <section className="panel">
          <div className="panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Scale size={18} color="var(--accent)" />
              <h3>Sources</h3>
            </div>
            <span className="badge badge-accent">{sources.length} configured</span>
          </div>
          <div className="panel-body" style={{ padding: '1.25rem', fontSize: '0.85rem' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
              <strong>Tier 1</strong> — regulators &amp; standards · <strong>Tier 2</strong> — vendor portals
            </p>
            {tier1.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text)' }}>Tier 1</div>
                <KeywordTags items={tier1.map((s) => s.organization || s.name)} max={12} />
              </div>
            )}
            {tier2.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text)' }}>Tier 2</div>
                <KeywordTags items={tier2.map((s) => s.organization || s.name)} max={8} />
              </div>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>Search keywords</h3>
          </div>
          <div className="panel-body" style={{ padding: '1.25rem', fontSize: '0.85rem' }}>
            {keywords ? (
              <>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{keywords.priority}</p>
                <KeywordTags items={keywords.primary.slice(0, 12)} />
                {keywords.fallback.frameworks.length > 0 && (
                  <div style={{ marginTop: '1.25rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text)' }}>Frameworks</div>
                    <KeywordTags items={keywords.fallback.frameworks.slice(0, 10)} />
                  </div>
                )}
              </>
            ) : (
              <p className="empty-state">Keywords unavailable</p>
            )}
          </div>
        </section>
      </div>

      <section className="config-section">
        <h3>Fetch compliance updates</h3>
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
            <label>Lookback days</label>
            <input type="number" value={lookback} onChange={(e) => setLookback(Number(e.target.value))} />
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
            <label>Min SAINT score (0–100)</label>
            <input type="number" min={0} max={100} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
          </div>
          <button type="button" className="btn btn-primary" onClick={runSearch} disabled={searching} style={{ height: '42px' }}>
            <Play size={16} /> {searching ? 'Fetching…' : 'POST /compliance/search'}
          </button>
        </div>
      </section>

      <div className="filter-bar">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.organization || s.name} (T{s.tier})
            </option>
          ))}
        </select>
        <select value={sourceTier} onChange={(e) => setSourceTier(e.target.value)}>
          <option value="">All tiers</option>
          <option value="1">Tier 1 only</option>
          <option value="2">Tier 2 only</option>
        </select>
        <input
          type="text"
          placeholder="Framework filter (e.g. GDPR)"
          value={framework}
          onChange={(e) => setFramework(e.target.value)}
          style={{ minWidth: 160 }}
        />
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header"><h3>Compliance findings</h3></div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Org</th>
                <th>Framework</th>
                <th>Title</th>
                <th>Flags</th>
                <th>Risk</th>
                <th>Score</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} onClick={() => setSelected(row)} style={{ cursor: 'pointer', background: selected?.id === row.id ? 'var(--accent-soft)' : undefined }}>
                  <td style={{ fontSize: '0.8rem' }}>{row.organization || row.source_name}</td>
                  <td style={{ fontSize: '0.75rem' }}>{row.frameworks[0] || '—'}</td>
                  <td className="title-cell">{row.title.slice(0, 48)}{row.title.length > 48 ? '…' : ''}</td>
                  <td>
                    {row.is_new_requirement && <span className="badge badge-danger" style={{ marginRight: 4 }}>new</span>}
                    {row.is_framework_update && <span className="badge badge-warning">update</span>}
                  </td>
                  <td><span className="badge badge-neutral">{row.risk_level}</span></td>
                  <td className={`score ${saintScoreClass(row.confidence_score)}`}>{saintScore(row.confidence_score)}</td>
                  <td>{formatDate(row.published_at)}</td>
                </tr>
              ))}
              {!items.length && (
                <tr><td colSpan={7} className="empty-state">No compliance records — run fetch</td></tr>
              )}
            </tbody>
          </table>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>Detail</h3>
            {selected && (
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => alert('Edit functionality coming soon')}>
                <Edit2 size={14} /> Edit
              </button>
            )}
          </div>
          <div className="panel-body" style={{ padding: '1.25rem' }}>
            {selected ? (
              <>
                <h4 style={{ marginBottom: 8 }}>{selected.title}</h4>
                <DetailGrid
                  rows={[
                    { label: 'Organization', value: selected.organization },
                    { label: 'Source', value: `${selected.source_name} (T${selected.source_tier})` },
                    { label: 'Subtype', value: selected.source_subtype },
                    { label: 'Risk level', value: selected.risk_level },
                    { label: 'SAINT score', value: `${saintScore(selected.confidence_score)} / 100` },
                    {
                      label: 'Trust / keyword / recency',
                      value: `${selected.source_trust_score.toFixed(0)} · ${selected.keyword_match_score.toFixed(0)} · ${selected.recency_score.toFixed(0)}`,
                    },
                    { label: 'New requirement', value: selected.is_new_requirement ? 'Yes' : 'No' },
                    { label: 'Framework update', value: selected.is_framework_update ? 'Yes' : 'No' },
                    { label: 'Author', value: selected.author },
                    { label: 'Published', value: formatDate(selected.published_at) },
                    { label: 'Score reason', value: selected.score_reason || '—' },
                  ]}
                />
                {selected.frameworks.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Frameworks</strong>
                    <KeywordTags items={selected.frameworks} />
                  </div>
                )}
                {selected.framework_versions.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Versions</strong>
                    <KeywordTags items={selected.framework_versions} />
                  </div>
                )}
                {selected.effective_dates.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Effective dates</strong>
                    <KeywordTags items={selected.effective_dates} />
                  </div>
                )}
                {selected.compliance_deadlines.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Deadlines</strong>
                    <KeywordTags items={selected.compliance_deadlines} />
                  </div>
                )}
                {selected.impacted_controls.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Impacted controls</strong>
                    <KeywordTags items={selected.impacted_controls} max={12} />
                  </div>
                )}
                {selected.matched_compliance_keywords.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Compliance keywords</strong>
                    <KeywordTags items={selected.matched_compliance_keywords} />
                  </div>
                )}
                {selected.matched_privacy_keywords.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Privacy keywords</strong>
                    <KeywordTags items={selected.matched_privacy_keywords} />
                  </div>
                )}
                {selected.matched_ai_keywords.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>AI governance</strong>
                    <KeywordTags items={selected.matched_ai_keywords} />
                  </div>
                )}
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 12 }}>
                  {selected.content.slice(0, 600)}
                </p>
                {selected.url && (
                  <p><a href={selected.url} target="_blank" rel="noreferrer">Open source</a></p>
                )}
                {selected.score_breakdown && Object.keys(selected.score_breakdown).length > 0 && (
                  <pre className="mono" style={{ fontSize: '0.75rem', marginTop: 12, overflow: 'auto' }}>
                    {JSON.stringify(selected.score_breakdown, null, 2)}
                  </pre>
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
