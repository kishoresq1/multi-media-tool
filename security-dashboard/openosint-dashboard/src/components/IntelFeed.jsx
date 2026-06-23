import { useState } from 'react'
import { AlertCircle, CheckCircle, ExternalLink, Megaphone } from 'lucide-react'
import ThreatBadge from './ThreatBadge.jsx'

function timeAgo(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function IntelRow({ item, onQueued }) {
  const [marking, setMarking] = useState(false)
  const [used, setUsed] = useState(item.usedInMarketing)
  const [ready, setReady] = useState(item.readyForMarketing)
  const [handoffStatus, setHandoffStatus] = useState('')
  const [campaignResult, setCampaignResult] = useState(null)

  async function handleMarkUsed() {
    if (used || ready || marking) return
    setMarking(true)
    setCampaignResult(null)
    setHandoffStatus('Sending this intel item to the Marketing queue.')
    try {
      const res = await fetch(`/api/intel/${item.id}/push-to-marketing`, { method: 'POST' })
      const data = await res.json().catch(() => ({}))
      if (res.ok && data.success) {
        setReady(true)
        onQueued?.(item.id)
        setCampaignResult({ ok: true, url: data.marketingFrontendUrl })
        setHandoffStatus('Ready in Marketing queue.')
      } else {
        setCampaignResult({ ok: false, error: data.error || 'Marketing API unavailable' })
        setHandoffStatus('Marketing queue handoff failed.')
      }
    } catch {
      setCampaignResult({ ok: false, error: 'Marketing API unavailable' })
      setHandoffStatus('Marketing queue handoff failed. Try again.')
    } finally {
      setMarking(false)
    }
  }

  const sourceUrl = item.sourceUrl || item.url

  return (
    <article className="intel-row">
      <div>
        <div className="inline-group">
          <ThreatBadge severity={item.severity} classification={item.classification} />
          <span className="row-meta">{timeAgo(item.timestamp)}</span>
          {item.source && <span className="row-meta">{item.source}</span>}
        </div>

        <div className="row-title" style={{ marginTop: 8 }}>{item.title}</div>

        {item.summary && item.summary !== item.title && (
          <p className="row-summary">
            {item.summary.slice(0, 220)}{item.summary.length > 220 ? ' Continued in source.' : ''}
          </p>
        )}

        {item.cveIds?.length > 0 && (
          <div className="inline-group" style={{ marginTop: 10 }}>
            {item.cveIds.map(cve => <span key={cve} className="code-pill">{cve}</span>)}
          </div>
        )}

        <div className="row-footer">
          <div className="inline-group">
            {item.sourceVerified ? (
              <span className="row-meta inline-group"><CheckCircle size={14} /> Verified source</span>
            ) : (
              <span className="row-meta inline-group"><AlertCircle size={14} /> Needs source check</span>
            )}
            {item.isMisinformation && <span className="threat-badge misinformation">Misinformation risk</span>}
          </div>
        </div>
      </div>

      <div className="inline-group" style={{ justifyContent: 'flex-end', alignContent: 'start' }}>
        {sourceUrl && (
          <a className="btn subtle" href={sourceUrl} target="_blank" rel="noreferrer" aria-label={`Open source for ${item.title}`}>
            <ExternalLink size={14} />
            Source
          </a>
        )}
        {!item.isMisinformation && (
          <button
            className={used || ready ? 'btn subtle' : 'btn primary'}
            onClick={handleMarkUsed}
            disabled={used || ready || marking}
            aria-describedby={`handoff-${item.id}`}
          >
            <Megaphone size={14} />
            {used ? 'Used in Marketing' : ready ? 'Ready in Marketing' : marking ? 'Sending to Marketing' : 'Send to Marketing'}
          </button>
        )}
        {handoffStatus && (
          <div className="inline-group" id={`handoff-${item.id}`} role="status">
            <span className="row-meta">
              {handoffStatus}
              {campaignResult?.ok === false && campaignResult.error ? ` ${campaignResult.error}.` : ''}
            </span>
            {campaignResult?.ok && campaignResult.url && (
              <a className="btn subtle" href={campaignResult.url} target="_blank" rel="noreferrer">
                <ExternalLink size={14} />
                Open Marketing
              </a>
            )}
          </div>
        )}
      </div>
    </article>
  )
}

export default function IntelFeed({ items = [], onQueued, loading = false }) {
  if (loading) {
    return <div className="loading-state">Loading threat review queue.</div>
  }

  if (!items.length) {
    return (
      <div className="empty-state">
        No threat items are in the queue. Run a feed scan or add client monitoring inputs to populate this desk.
      </div>
    )
  }

  return (
    <div className="queue-list">
      {items.map(item => <IntelRow key={item.id} item={item} onQueued={onQueued} />)}
    </div>
  )
}
