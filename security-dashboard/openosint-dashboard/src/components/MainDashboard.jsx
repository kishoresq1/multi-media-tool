import { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Building2, Database, RefreshCw, ShieldCheck } from 'lucide-react'
import IntelFeed from './IntelFeed.jsx'
import CustomerIntelligenceWidget from './CustomerIntelligenceWidget.jsx'

function MetricCard({ icon: Icon, label, value, note }) {
  return (
    <div className="metric-card">
      <div className="metric-topline">
        <span>{label}</span>
        <Icon size={18} />
      </div>
      <div className="metric-value">{value}</div>
      {note && <div className="metric-note">{note}</div>}
    </div>
  )
}

function StatusPill({ active, label }) {
  return (
    <span className="status-pill">
      <span className={`status-dot ${active ? 'online' : 'offline'}`} />
      {label}
    </span>
  )
}

export default function MainDashboard() {
  const [intel, setIntel] = useState([])
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [apiOnline, setApiOnline] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)

  const fetchData = useCallback(async (signal) => {
    try {
      const [healthRes, intelRes, companiesRes] = await Promise.all([
        fetch('/health', { signal }).catch(() => null),
        fetch('/api/intel/latest?limit=20', { signal }),
        fetch('/api/companies', { signal }),
      ])

      if (signal?.aborted) return
      setApiOnline(Boolean(healthRes?.ok))
      if (intelRes.ok) setIntel(await intelRes.json())
      if (companiesRes.ok) setCompanies(await companiesRes.json())
      setLastRefresh(new Date())
    } catch (error) {
      if (error?.name === 'AbortError') return
      setApiOnline(false)
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetchData(controller.signal)
    const interval = setInterval(() => fetchData(controller.signal), 30000)
    return () => {
      controller.abort()
      clearInterval(interval)
    }
  }, [fetchData])

  const criticals = intel.filter(item => item.severity === 'CRITICAL').length
  const darkWebHits = intel.filter(item => item.classification === 'BREACH').length
  const marketingReady = intel.filter(item => item.readyForMarketing && !item.usedInMarketing).length

  const highestRiskCompany = useMemo(() => {
    return [...companies].sort((a, b) => (b.threatScore || 0) - (a.threatScore || 0))[0]
  }, [companies])

  return (
    <div>
      <header className="page-header">
        <div>
          <div className="eyebrow">Client watch desk</div>
          <h1>Client Intelligence Operations</h1>
          <p className="header-copy">
            Monitor client exposure, triage verified threats, and move approved intelligence into
            notification and catapult asset workflows.
          </p>
        </div>

        <div className="status-strip">
          <StatusPill active={apiOnline} label={apiOnline ? 'API online' : 'API offline'} />
          <span className="status-pill">
            {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : 'Refresh pending'}
          </span>
        </div>
      </header>

      <section className="metrics-grid" aria-label="Operational summary">
        <MetricCard icon={ShieldCheck} label="Intel items" value={intel.length} note="Latest queue load" />
        <MetricCard icon={AlertTriangle} label="Critical CVEs" value={criticals} note="Needs review first" />
        <MetricCard icon={Building2} label="Clients watched" value={companies.length} note={highestRiskCompany ? `Highest: ${highestRiskCompany.name}` : 'No clients loaded'} />
        <MetricCard icon={Database} label="Marketing ready" value={marketingReady} note={`${darkWebHits} breach-class items`} />
      </section>

      <section className="section">
        <CustomerIntelligenceWidget />
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <h2>Threat Review Queue</h2>
            <div className="section-kicker">Verified items are ready for client notice and asset handoff.</div>
          </div>
          <button className="btn subtle" onClick={() => fetchData()} aria-label="Refresh threat review queue">
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>

        <div className="panel">
          <IntelFeed
            items={intel}
            loading={loading}
            onQueued={id => setIntel(prev => prev.map(item => item.id === id ? { ...item, readyForMarketing: true } : item))}
          />
        </div>
      </section>
    </div>
  )
}
