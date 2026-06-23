import { useEffect, useState } from 'react'
import { Radio, WifiOff, Briefcase, Camera, Globe, MessageSquare, Share2 } from 'lucide-react'
import { api, API_BASE } from '../api/client'
import type { Advisory, BlogPost, BreachIntel, ComplianceIntel, IntelPost, UnifiedIntel, VulnIntel } from '../api/client'
import { StatCard } from '../components/StatCard'
import { ClassificationBadge } from '../components/shared'
import { formatDate, saintScore, saintScoreClass } from '../lib/format'
import { Link } from 'react-router-dom'

export function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [apiOk, setApiOk] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [social, setSocial] = useState<IntelPost[]>([])
  const [advisories, setAdvisories] = useState<Advisory[]>([])
  const [vulns, setVulns] = useState<VulnIntel[]>([])
  const [blogs, setBlogs] = useState<BlogPost[]>([])
  const [breaches, setBreaches] = useState<BreachIntel[]>([])
  const [unified, setUnified] = useState<UnifiedIntel[]>([])
  const [unifiedTotal, setUnifiedTotal] = useState(0)
  const [breachTotal, setBreachTotal] = useState(0)
  const [compliance, setCompliance] = useState<ComplianceIntel[]>([])
  const [complianceTotal, setComplianceTotal] = useState(0)
  const [health, setHealth] = useState({ sources: 0, version: '—' })

  const load = async () => {
    const ping = await api.ping()
    setApiOk(ping.ok)
    if (!ping.ok) {
      setApiError(ping.error ?? 'API unreachable')
      setLoading(false)
      return
    }
    setApiError(null)

    const data = await api.dashboardBundle()
    if (data.health) {
      setHealth({ sources: data.health.sources_enabled, version: data.health.version })
    }
    setSocial(data.social.posts)
    setAdvisories(data.advisories.advisories)
    setVulns(data.vulns.items)
    setBlogs(data.blogs.posts)
    setBreaches(data.breaches.items)
    setBreachTotal(data.breaches.total)
    setCompliance(data.compliance.items)
    setComplianceTotal(data.compliance.total)
    setUnified(data.unified.items)
    setUnifiedTotal(data.unified.total)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <div className="loading">Connecting to API at {API_BASE}…</div>

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Security overview</h2>
          <p>Live view of social signals, vendor advisories, vulnerability feeds, and researcher blogs from the last 30 days.</p>
        </div>
      </div>

      {!apiOk && (
        <div className="error-banner">
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <WifiOff size={16} /> {apiError}
            <br />
            <small style={{ marginTop: 4, display: 'block' }}>
              Start backend: <code>cd backend && uvicorn app.main:app --reload --port 8009</code>
            </small>
          </span>
        </div>
      )}

      {apiError && apiOk && <div className="error-banner">{apiError}</div>}

      <div className="stat-grid" style={{ marginBottom: '2rem' }}>
        <Link to="/social" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Social feeds" value={social.length} meta="View all →" />
        </Link>
        <Link to="/advisories" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Advisories" value={advisories.length} meta="View all →" />
        </Link>
        <Link to="/vulnerabilities" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Vulnerabilities" value={vulns.length} meta="View all →" />
        </Link>
        <Link to="/blogs" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Research blogs" value={blogs.length} meta="View all →" />
        </Link>
        <Link to="/compliance" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Compliance" value={complianceTotal} meta="Regulatory →" />
        </Link>
        <Link to="/breaches" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Company breaches" value={breachTotal} meta="View all →" />
        </Link>
        <Link to="/unified" style={{ textDecoration: 'none', color: 'inherit' }}>
          <StatCard label="Unified intel" value={unifiedTotal} meta="Classified view →" />
        </Link>
        <StatCard label="Sources active" value={health.sources} meta={`API v${health.version}`} />
      </div>

      <div className="page-header" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Share2 size={20} color="var(--accent)" />
          <h3>Social publishing channels</h3>
        </div>
        <p>Status of automated and manual intelligence sharing across social platforms.</p>
      </div>

      <div className="grid-4" style={{ marginBottom: '2.5rem' }}>
        <div className="stat-card" style={{ borderLeft: '4px solid #0a66c2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <div className="stat-card-label">LinkedIn</div>
            <Briefcase size={20} color="#0a66c2" />
          </div>
          <div className="stat-card-value" style={{ color: '#0a66c2' }}>3</div>
          <div className="stat-card-meta">
            Posts published · <Link to="/integrations" style={{ color: 'inherit', textDecoration: 'underline' }}>Manage</Link>
          </div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #e4405f' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <div className="stat-card-label">Instagram</div>
            <Camera size={20} color="#e4405f" />
          </div>
          <div className="stat-card-value">0</div>
          <div className="stat-card-meta">
            Posts published · <Link to="/integrations" style={{ color: 'inherit', textDecoration: 'underline' }}>View</Link>
          </div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #1877f2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <div className="stat-card-label">Facebook</div>
            <Globe size={20} color="#1877f2" />
          </div>
          <div className="stat-card-value">0</div>
          <div className="stat-card-meta">
            Posts published · <Link to="/integrations" style={{ color: 'inherit', textDecoration: 'underline' }}>View</Link>
          </div>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #000000' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <div className="stat-card-label">X / Twitter</div>
            <MessageSquare size={20} color="#000000" />
          </div>
          <div className="stat-card-value">0</div>
          <div className="stat-card-meta">
            Posts published · <Link to="/integrations" style={{ color: 'inherit', textDecoration: 'underline' }}>Manage</Link>
          </div>
        </div>
      </div>

      {!apiOk ? null : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="grid-2">
            <section className="panel">
              <div className="panel-header">
                <h3><Radio size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} />Latest advisories</h3>
                <span className="badge badge-accent">Vendor</span>
              </div>
              <div className="panel-body">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Score</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {advisories.map((a) => (
                      <tr key={a.id}>
                        <td className="title-cell">
                          {a.url ? <a href={a.url} target="_blank" rel="noreferrer">{a.title}</a> : a.title}
                          {a.vendor && <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{a.vendor}</div>}
                        </td>
                        <td className={`score ${saintScoreClass(a.confidence_score)}`}>{saintScore(a.confidence_score)}</td>
                        <td>{formatDate(a.published_at)}</td>
                      </tr>
                    ))}
                    {!advisories.length && (
                      <tr><td colSpan={3} className="empty-state">No advisories yet — run collection</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h3>CVEs & vulnerabilities</h3>
                <span className="badge badge-warning">NVD / KEV</span>
              </div>
              <div className="panel-body">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>CVE / Title</th>
                      <th>Source</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vulns.map((v) => (
                      <tr key={v.id}>
                        <td className="title-cell">
                          {v.cve_id && <span className="mono">{v.cve_id}</span>}
                          <div style={{ fontSize: '0.8rem', marginTop: 2 }}>{v.title.slice(0, 60)}…</div>
                          {v.in_cisa_kev && <span className="badge badge-danger" style={{ marginTop: 4 }}>KEV</span>}
                        </td>
                        <td>{v.source_name}</td>
                        <td>{formatDate(v.published_at)}</td>
                      </tr>
                    ))}
                    {!vulns.length && (
                      <tr><td colSpan={3} className="empty-state">No vulnerability records</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <div className="grid-3">
            <section className="panel">
              <div className="panel-header">
                <h3>Compliance updates</h3>
                <span className="badge badge-accent">Regulatory</span>
              </div>
              <div className="panel-body">
                <table className="data-table">
                  <thead>
                    <tr><th>Org</th><th>Framework</th><th>Title</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    {compliance.map((c) => (
                      <tr key={c.id}>
                        <td>{c.organization || c.source_name}</td>
                        <td style={{ fontSize: '0.8rem' }}>{c.frameworks[0] || '—'}</td>
                        <td className="title-cell">{c.title.slice(0, 30)}…</td>
                        <td className={`score ${saintScoreClass(c.confidence_score)}`}>{saintScore(c.confidence_score)}</td>
                      </tr>
                    ))}
                    {!compliance.length && (
                      <tr><td colSpan={4} className="empty-state">No compliance records</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h3>Latest breaches</h3>
                <span className="badge badge-danger">Company</span>
              </div>
              <div className="panel-body">
                <table className="data-table">
                  <thead>
                    <tr><th>Company</th><th>Title</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    {breaches.map((b) => (
                      <tr key={b.id}>
                        <td>{b.affected_company || '—'}</td>
                        <td className="title-cell">{b.title.slice(0, 40)}…</td>
                        <td className={`score ${saintScoreClass(b.confidence_score)}`}>{saintScore(b.confidence_score)}</td>
                      </tr>
                    ))}
                    {!breaches.length && (
                      <tr><td colSpan={3} className="empty-state">No breach records</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h3>Unified intel</h3>
                <span className="badge badge-accent">SAINT</span>
              </div>
              <div className="panel-body">
                <table className="data-table">
                  <thead>
                    <tr><th>Type</th><th>Title</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    {unified.map((u) => (
                      <tr key={u.id}>
                        <td><ClassificationBadge type={u.classification} /></td>
                        <td className="title-cell">{u.title.slice(0, 40)}…</td>
                        <td className={`score ${saintScoreClass(u.confidence_score)}`}>{saintScore(u.confidence_score)}</td>
                      </tr>
                    ))}
                    {!unified.length && (
                      <tr><td colSpan={3} className="empty-state">Run unified rebuild</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <section className="panel">
            <div className="panel-header">
              <h3>Social & research signals</h3>
            </div>
            <div className="panel-body">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Platform</th>
                    <th>Title</th>
                    <th>Score</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {[...social, ...blogs.map((b) => ({
                    id: b.id,
                    platform: 'blog',
                    source_name: b.source_name,
                    title: b.title,
                    url: b.url,
                    confidence_score: b.confidence_score,
                    published_at: b.published_at,
                  }))].slice(0, 10).map((row) => (
                    <tr key={row.id}>
                      <td><span className="badge badge-neutral">{row.platform || row.source_name}</span></td>
                      <td className="title-cell">
                        {row.url ? <a href={row.url} target="_blank" rel="noreferrer">{row.title}</a> : row.title}
                      </td>
                      <td className={`score ${saintScoreClass(row.confidence_score)}`}>{saintScore(row.confidence_score)}</td>
                      <td>{formatDate(row.published_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </>
  )
}
