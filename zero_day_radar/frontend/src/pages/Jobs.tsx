import { useEffect, useState } from 'react'
import { Play, Pause, RefreshCw, Clock, CheckCircle2, AlertCircle } from 'lucide-react'
import { api, ApiError } from '../api/client'
import { ErrorBanner, Loading, PageHeader } from '../components/shared'

const INITIAL_PIPELINES = [
  { id: 'all', label: 'All pipelines', desc: 'Social + advisories + blogs + vulnerabilities' },
  { id: 'social', label: 'Social', desc: 'Twitter, Reddit, HN, LinkedIn' },
  { id: 'advisories', label: 'Advisories', desc: 'Vendor security bulletins' },
  { id: 'blogs', label: 'Blogs', desc: 'Researcher blogs' },
  { id: 'vulnerabilities', label: 'Vulnerabilities', desc: 'CVE, NVD, KEV, GitHub' },
  { id: 'compliance', label: 'Compliance', desc: 'NIST, ISO, PCI SSC, GDPR, EU AI Act' },
  { id: 'breaches', label: 'Breaches', desc: 'Krebs, BleepingComputer, Ransomware.live' },
  { id: 'unified', label: 'Unified intel', desc: 'Rebuild classified unified_intel table' },
]

export function Jobs() {
  const [config, setConfig] = useState<Record<string, any> | null>(null)
  const [worker, setWorker] = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<Record<string, any> | null>(null)
  const [queuing, setQueuing] = useState<string | null>(null)

  // UI-only state for job status
  const [jobStatuses, setJobStatuses] = useState<Record<string, 'running' | 'paused'>>(() => {
    const initial: Record<string, 'running' | 'paused'> = {}
    INITIAL_PIPELINES.forEach(p => {
      initial[p.id] = 'running'
    })
    return initial
  })

  const load = async () => {
    try {
      const [cfg, wh] = await Promise.all([
        api.jobsConfig(),
        api.workerHealth().catch(() => null),
      ])
      setConfig(cfg)
      setWorker(wh as Record<string, any> | null)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const run = async (pipeline: string) => {
    if (jobStatuses[pipeline] === 'paused') {
      alert('Cannot trigger a paused job. Please resume it first.')
      return
    }
    setQueuing(pipeline)
    setError(null)
    try {
      const res = await api.triggerJob(pipeline)
      setTaskId(res.task_id)
      setTaskStatus({ status: res.status, message: res.message })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to queue job')
    } finally {
      setQueuing(null)
    }
  }

  const toggleJobStatus = (id: string) => {
    setJobStatuses(prev => ({
      ...prev,
      [id]: prev[id] === 'running' ? 'paused' : 'running'
    }))
  }

  const checkStatus = async () => {
    if (!taskId) return
    try {
      const res = await api.jobStatus(taskId)
      setTaskStatus(res as unknown as Record<string, any>)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Status check failed')
    }
  }

  if (loading) return <Loading />

  return (
    <>
      <PageHeader
        title="Background jobs"
        description="Manage automated intelligence collection pipelines and scheduler status."
        actions={<button type="button" className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />
      {error && <ErrorBanner message={error} />}

      <div className="stat-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-card-label">Worker Status</div>
            {config?.celery_enabled ? <CheckCircle2 size={18} color="var(--success)" /> : <AlertCircle size={18} color="var(--danger)" />}
          </div>
          <div className="stat-card-value">{config?.celery_enabled ? 'Active' : 'Offline'}</div>
          <div className="stat-card-meta">Celery + Redis backend</div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-card-label">Scheduler</div>
            <Clock size={18} color="var(--accent)" />
          </div>
          <div className="stat-card-value">Every {String(config?.beat_interval_minutes ?? 20)}m</div>
          <div className="stat-card-meta">Next run in ~12 min</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Active Pipelines</div>
          <div className="stat-card-value">{Object.values(jobStatuses).filter(s => s === 'running').length} / {INITIAL_PIPELINES.length}</div>
          <div className="stat-card-meta">Jobs currently enabled</div>
        </div>
      </div>

      <section className="config-section">
        <h3>Pipeline Management</h3>
        <div className="integration-grid" style={{ marginTop: '1.5rem' }}>
          {INITIAL_PIPELINES.map((p) => {
            const status = jobStatuses[p.id]
            const isRunning = status === 'running'
            return (
              <div key={p.id} className="integration-card" style={{ opacity: isRunning ? 1 : 0.75 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <h4 style={{ margin: 0 }}>{p.label}</h4>
                  <span className={`badge ${isRunning ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                    {isRunning ? 'Running' : 'Paused'}
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', marginBottom: '1.25rem' }}>{p.desc}</p>
                
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ flex: 2 }}
                    onClick={() => run(p.id)}
                    disabled={queuing === p.id || !isRunning}
                  >
                    <Play size={14} /> {queuing === p.id ? 'Queuing…' : 'Run Now'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ flex: 1, padding: '0.5rem' }}
                    onClick={() => toggleJobStatus(p.id)}
                    title={isRunning ? 'Pause job' : 'Resume job'}
                  >
                    {isRunning ? <Pause size={14} /> : <Play size={14} />}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {taskId && (
        <section className="config-section">
          <h3>Last execution details</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: '1rem' }}>
            <p className="mono" style={{ fontSize: '0.85rem', margin: 0 }}>Task ID: {taskId}</p>
            <button type="button" className="btn btn-ghost btn-sm" onClick={checkStatus}>
              <RefreshCw size={14} /> Refresh Status
            </button>
          </div>
          {taskStatus && (
            <pre style={{ background: 'var(--bg)', padding: '1.25rem', borderRadius: 8, fontSize: '0.8rem', overflow: 'auto', border: '1px solid var(--border)' }}>
              {JSON.stringify(taskStatus, null, 2)}
            </pre>
          )}
        </section>
      )}
    </>
  )
}
