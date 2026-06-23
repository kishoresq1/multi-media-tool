import { useCallback, useEffect, useState } from 'react'
import { Briefcase, Edit2, Play, RefreshCw, Sparkles } from 'lucide-react'
import {
  api,
  API_BASE,
  ApiError,
  linkedinLoginUrl,
  type LinkedInPostPreview,
  type LinkedInStatus,
  type UnifiedIntel,
} from '../api/client'
import {
  ClassificationBadge,
  DetailGrid,
  ErrorBanner,
  KeywordTags,
  Loading,
  PageHeader,
  SuccessBanner,
} from '../components/shared'
import { formatDate, saintScore, saintScoreClass } from '../lib/format'
import {
  buildLinkedInPostFromDetail,
  LINKEDIN_PENDING_POST_KEY,
} from '../lib/linkedinPost'

const CLASSIFICATIONS = [
  '',
  'PRODUCT_VULNERABILITY',
  'COMPANY_BREACH',
  'UNKNOWN',
]

export function UnifiedIntelPage() {
  const [items, setItems] = useState<UnifiedIntel[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [classifying, setClassifying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selected, setSelected] = useState<UnifiedIntel | null>(null)
  const [classification, setClassification] = useState('')
  const [classifyText, setClassifyText] = useState('')
  const [classifyResult, setClassifyResult] = useState<string | null>(null)

  const [linkedin, setLinkedin] = useState<LinkedInStatus | null>(null)
  const [postModalOpen, setPostModalOpen] = useState(false)
  const [postPreview, setPostPreview] = useState<LinkedInPostPreview | null>(null)
  const [humanVerified, setHumanVerified] = useState(false)
  const [posting, setPosting] = useState(false)
  const [postStep, setPostStep] = useState<'review' | 'confirm'>('review')
  const [postError, setPostError] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'text' | 'image' | 'video'>('image')

  const loadLinkedin = useCallback(async () => {
    try {
      const status = await api.linkedinStatus()
      setLinkedin(status)
    } catch {
      setLinkedin(null)
    }
  }, [])

  const load = useCallback(async () => {
    setError(null)
    try {
      const res = await api.unified({
        classification: classification || undefined,
        min_score: 0,
        limit: 100,
      })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [classification])

  const commentaryForMedia = useCallback(
    (row: UnifiedIntel, format: 'text' | 'image' | 'video') =>
      buildLinkedInPostFromDetail(row, { includeHashtags: format === 'text' }),
    [],
  )

  const openPostModalFor = useCallback(async (row: UnifiedIntel) => {
    const commentary = commentaryForMedia(row, mediaType)
    setPostModalOpen(true)
    setPostStep('review')
    setHumanVerified(false)
    setPostError(null)
    setPostPreview({
      unified_id: row.id,
      title: row.title,
      commentary,
      char_count: commentary.length,
    })
    try {
      const preview = await api.linkedinPreview(row.id, mediaType)
      setPostPreview(preview)
    } catch {
      /* keep client-built preview from detail panel */
    }
  }, [commentaryForMedia, mediaType])

  useEffect(() => {
    if (!postModalOpen || !selected) return
    const commentary = commentaryForMedia(selected, mediaType)
    setPostPreview((prev) =>
      prev ? { ...prev, commentary, char_count: commentary.length } : prev,
    )
    void api.linkedinPreview(selected.id, mediaType).then(setPostPreview).catch(() => {})
  }, [mediaType, postModalOpen, selected, commentaryForMedia])

  useEffect(() => { load(); loadLinkedin() }, [load, loadLinkedin])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const li = params.get('linkedin')
    if (li === 'connected') {
      const name = params.get('name')
      setSuccess(name ? `LinkedIn connected as ${name}` : 'LinkedIn connected')
      loadLinkedin().then(async () => {
        const pendingId = sessionStorage.getItem(LINKEDIN_PENDING_POST_KEY)
        sessionStorage.removeItem(LINKEDIN_PENDING_POST_KEY)
        if (pendingId) {
          try {
            const res = await api.unified({ min_score: 0, limit: 100 })
            const row = res.items.find((i) => i.id === pendingId)
            if (row) {
              setSelected(row)
              await openPostModalFor(row)
            }
          } catch { /* */ }
        }
      })
      window.history.replaceState({}, '', '/unified')
    } else if (li === 'error') {
      sessionStorage.removeItem(LINKEDIN_PENDING_POST_KEY)
      setError(params.get('message') || 'LinkedIn connection failed')
      window.history.replaceState({}, '', '/unified')
    }
  }, [loadLinkedin, openPostModalFor])

  const runPipeline = async () => {
    setRunning(true)
    setError(null)
    try {
      const res = await api.unifiedRun({ run_collections: false, use_llm: false })
      setSuccess(`Rebuilt ${res.items_saved} unified rows (${res.duration_seconds.toFixed(1)}s)`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Pipeline failed')
    } finally {
      setRunning(false)
    }
  }

  const runClassify = async () => {
    if (!classifyText.trim()) return
    setClassifying(true)
    setClassifyResult(null)
    try {
      const res = await api.classify({ title: classifyText.slice(0, 200), content: classifyText })
      setClassifyResult(
        `${res.incident_type} (${res.classification_confidence}%) — ${res.reason}` +
          (res.company_name ? ` · company: ${res.company_name}` : '') +
          (res.vendor_name ? ` · vendor: ${res.vendor_name}` : '') +
          (res.cve ? ` · ${res.cve}` : ''),
      )
    } catch (e) {
      setClassifyResult(e instanceof ApiError ? e.message : 'Classification failed')
    } finally {
      setClassifying(false)
    }
  }

  const connectAndPost = () => {
    if (!selected) return
    sessionStorage.setItem(LINKEDIN_PENDING_POST_KEY, selected.id)
    window.location.href = linkedinLoginUrl(linkedin)
  }

  const openPostModal = async () => {
    if (!selected) return
    if (!linkedin?.connected) {
      connectAndPost()
      return
    }
    await openPostModalFor(selected)
  }

  const closePostModal = () => {
    setPostModalOpen(false)
    setPostPreview(null)
    setHumanVerified(false)
    setPostStep('review')
    setPostError(null)
  }

  const proceedToConfirm = () => {
    if (!humanVerified) return
    setPostStep('confirm')
  }

  const confirmPost = async () => {
    if (!selected || !humanVerified || posting) return
    setPosting(true)
    setPostError(null)
    const format = mediaType
    try {
      const res = await api.linkedinPost({
        unified_id: selected.id,
        human_verified: true,
        commentary: postPreview?.commentary,
        media_type: format,
      })
      const kind = format === 'text' ? 'text' : format === 'image' ? 'image post' : 'video post'
      setSuccess(
        `Posted ${kind} to LinkedIn` +
          (res.media_urn ? ` · media attached` : '') +
          (res.linkedin_post_id ? ` (${res.linkedin_post_id})` : ''),
      )
      closePostModal()
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'LinkedIn post failed'
      setPostError(msg)
    } finally {
      setPosting(false)
    }
  }

  if (loading) return <Loading text="Loading unified intel…" />

  return (
    <>
      <PageHeader
        title="Unified intelligence"
        description="Consolidated findings with SAINT classification, threat/compliance scores, and entity extraction."
        actions={
          <button type="button" className="btn btn-secondary" onClick={load}>
            <RefreshCw size={16} /> Refresh
          </button>
        }
      />
      {error && <ErrorBanner message={error} />}
      {success && <SuccessBanner message={success} />}

      <section className="config-section linkedin-connect-bar">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Briefcase size={18} />
            <div>
              <strong>LinkedIn personal profile</strong>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {linkedin?.connected
                  ? `Connected as ${linkedin.display_name} · ${linkedin.post_mode} mode`
                  : 'Sign in with LinkedIn (OpenID Connect) to post unified intel to your feed'}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {linkedin?.connected ? (
              <button type="button" className="btn btn-ghost" onClick={() => api.linkedinDisconnect().then(loadLinkedin)}>
                Disconnect
              </button>
            ) : (
              <a className="btn btn-primary" href={linkedinLoginUrl(linkedin)}>
                Connect LinkedIn
              </a>
            )}
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Rebuild unified table</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 12 }}>
          Groups existing intel by vendor/product/CVE, classifies incidents, and writes to unified_intel.
        </p>
        <button type="button" className="btn btn-primary" onClick={runPipeline} disabled={running}>
          <Play size={16} /> {running ? 'Running…' : 'POST /unified/run'}
        </button>
      </section>

      <section className="config-section">
        <h3><Sparkles size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} />Try classifier</h3>
        <textarea
          rows={3}
          value={classifyText}
          onChange={(e) => setClassifyText(e.target.value)}
          placeholder="Paste headline or article excerpt…"
          style={{ width: '100%', marginBottom: 8 }}
        />
        <button type="button" className="btn btn-secondary" onClick={runClassify} disabled={classifying}>
          {classifying ? 'Classifying…' : 'POST /classify'}
        </button>
        {classifyResult && (
          <p style={{ marginTop: 8, fontSize: '0.85rem' }}>{classifyResult}</p>
        )}
      </section>

      <div className="filter-bar">
        <select value={classification} onChange={(e) => setClassification(e.target.value)}>
          {CLASSIFICATIONS.map((c) => (
            <option key={c || 'all'} value={c}>
              {c ? c.replace(/_/g, ' ') : 'All classifications'}
            </option>
          ))}
        </select>
        <span className="badge badge-neutral">{total} total</span>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header"><h3>Unified records</h3></div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Entity</th>
                <th>Score</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelected(row)}
                  style={{ cursor: 'pointer', background: selected?.id === row.id ? 'var(--accent-soft)' : undefined }}
                >
                  <td><ClassificationBadge type={row.classification} /></td>
                  <td className="title-cell">{row.title.slice(0, 55)}{row.title.length > 55 ? '…' : ''}</td>
                  <td style={{ fontSize: '0.8rem' }}>
                    {row.company_name || row.vendor_name || '—'}
                  </td>
                  <td className={`score ${saintScoreClass(row.confidence_score)}`}>
                    {saintScore(row.confidence_score)}
                  </td>
                  <td>{formatDate(row.latest_date)}</td>
                </tr>
              ))}
              {!items.length && (
                <tr><td colSpan={5} className="empty-state">No unified records — run rebuild</td></tr>
              )}
            </tbody>
          </table>
        </section>

        <section className="panel" id="unified-detail-panel">
          <div className="panel-header">
            <h3>Detail</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              {selected && (
                <>
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => alert('Edit functionality coming soon')}>
                    <Edit2 size={14} /> Edit
                  </button>
                  <button type="button" className="btn btn-primary btn-sm" onClick={openPostModal}>
                    <Briefcase size={14} />
                    {linkedin?.connected ? 'Post to LinkedIn' : 'Connect & Post'}
                  </button>
                </>
              )}
            </div>
          </div>
          <div className="panel-body" style={{ padding: '1.25rem' }}>
            {selected ? (
              <>
                <h4 style={{ marginBottom: 8 }}>{selected.title}</h4>
                <ClassificationBadge type={selected.classification} />
                <DetailGrid
                  rows={[
                    { label: 'Company', value: selected.company_name },
                    { label: 'Vendor', value: selected.vendor_name || '—' },
                    { label: 'Product', value: selected.product_name || '—' },
                    { label: 'Version', value: selected.version_name },
                    { label: 'Risk level', value: <span className="badge badge-warning">{selected.risk_level}</span> },
                    { label: 'Confidence', value: `${saintScore(selected.confidence_score)} / 100` },
                    { label: 'Threat score', value: selected.threat_score.toFixed(1) },
                    { label: 'Compliance score', value: selected.compliance_score.toFixed(1) },
                    {
                      label: 'Classification confidence',
                      value: `${selected.classification_confidence.toFixed(0)}%`,
                    },
                    { label: 'Classification reason', value: selected.classification_reason },
                    { label: 'Score reason', value: selected.score_reason || '—' },
                    { label: 'Sources', value: selected.source_count },
                    { label: 'Latest date', value: formatDate(selected.latest_date) },
                    { label: 'LLM enriched', value: selected.llm_enriched ? `Yes (${selected.llm_model})` : 'No' },
                  ]}
                />
                {selected.summary && (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 12 }}>
                    {selected.summary}
                  </p>
                )}
                {selected.llm_summary && (
                  <p style={{ fontSize: '0.85rem', marginTop: 8 }}>
                    <strong>LLM summary:</strong> {selected.llm_summary}
                  </p>
                )}
                {selected.cves.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>CVEs</strong>
                    <KeywordTags items={selected.cves} />
                  </div>
                )}
                {selected.frameworks.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong style={{ fontSize: '0.8rem' }}>Frameworks</strong>
                    <KeywordTags items={selected.frameworks} />
                  </div>
                )}
                {selected.score_breakdown && Object.keys(selected.score_breakdown).length > 0 && (
                  <pre className="mono" style={{ fontSize: '0.75rem', marginTop: 12, overflow: 'auto' }}>
                    {JSON.stringify(selected.score_breakdown, null, 2)}
                  </pre>
                )}
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                  <button type="button" className="btn btn-primary" onClick={openPostModal}>
                    <Briefcase size={16} />
                    {linkedin?.connected ? 'Post to LinkedIn' : 'Connect & Post'}
                  </button>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 8 }}>
                    Post as text, image card, or video slideshow — two-step verification required.
                  </p>
                </div>
              </>
            ) : (
              <p className="empty-state">Select a row</p>
            )}
          </div>
        </section>
      </div>

      {postModalOpen && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="linkedin-post-title">
          <div className="modal-card">
            <h3 id="linkedin-post-title">
              {postStep === 'review' ? 'Review LinkedIn post' : 'Confirm & post'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {postStep === 'review'
                ? 'Choose format, review the preview, then confirm.'
                : `Final step — publish ${mediaType === 'video' ? 'video + caption' : mediaType === 'image' ? 'image + caption' : 'text'} to LinkedIn.`}
            </p>

            <div className="media-type-tabs" style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
              {(['text', 'image', 'video'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`btn ${mediaType === t ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setMediaType(t)}
                  disabled={postStep === 'confirm'}
                >
                  {t === 'text' ? 'Text only' : t === 'image' ? 'Image card' : 'Video'}
                </button>
              ))}
              <span className="badge badge-accent" style={{ marginLeft: 'auto' }}>
                Will post: {mediaType === 'image' ? 'Image + caption' : mediaType === 'video' ? 'Video + caption' : 'Text only'}
              </span>
            </div>

            {postPreview ? (
              <>
                {mediaType === 'image' && selected && (
                  <div style={{ marginBottom: 12 }}>
                    <img
                      key={selected.id}
                      src={`${API_BASE}/linkedin/media/${selected.id}/image?t=${selected.id}`}
                      alt="Generated intel card"
                      style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
                    />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>
                      PNG card auto-generated from detail panel
                    </p>
                  </div>
                )}
                {mediaType === 'video' && selected && (
                  <div style={{ marginBottom: 12 }}>
                    <video
                      key={selected.id}
                      src={`${API_BASE}/linkedin/media/${selected.id}/video?t=${selected.id}`}
                      controls
                      style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
                    />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>
                      10s video — same card as image with slow zoom (matches LinkedIn post)
                    </p>
                  </div>
                )}
                <div className="form-group" style={{ marginTop: '1.25rem' }}>
                  <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    Post Commentary
                    <span style={{ fontSize: '0.7rem', fontWeight: 400, color: 'var(--text-muted)' }}>
                      {postPreview.char_count} / 3000
                    </span>
                  </label>
                  <textarea
                    className="linkedin-preview-box"
                    style={{ width: '100%', height: '160px', margin: 0, resize: 'vertical' }}
                    value={postPreview.commentary}
                    onChange={(e) => setPostPreview({
                      ...postPreview,
                      commentary: e.target.value,
                      char_count: e.target.value.length
                    })}
                    disabled={postStep === 'confirm'}
                  />
                </div>
              </>
            ) : (
              <div className="loading" style={{ margin: '1rem 0' }}>Building post from detail…</div>
            )}

            {postError && (
              <div className="error-banner" style={{ marginTop: 12 }}>
                {postError}
              </div>
            )}

            {postStep === 'review' && (
              <label className="human-verify-check">
                <input
                  type="checkbox"
                  checked={humanVerified}
                  onChange={(e) => setHumanVerified(e.target.checked)}
                />
                I have reviewed this content and approve posting it to my LinkedIn profile
              </label>
            )}

            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={closePostModal} disabled={posting}>
                Cancel
              </button>
              {postStep === 'review' ? (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={proceedToConfirm}
                  disabled={!humanVerified || !postPreview}
                >
                  Continue to post
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={confirmPost}
                  disabled={posting || !humanVerified || !postPreview}
                >
                  {posting
                    ? `Posting ${mediaType}…`
                    : `Post ${mediaType === 'image' ? 'image' : mediaType === 'video' ? 'video' : 'text'} to LinkedIn`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
