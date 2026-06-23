import { useCallback, useEffect, useMemo, useState } from 'react'
import { Building2, RefreshCw, Target, Users } from 'lucide-react'

const emptySummary = {
  total_leads: 0,
  hot_leads: 0,
  warm_leads: 0,
  companies_identified: 0,
  leads: [],
}

function categoryClass(category) {
  if (category === 'Hot Lead') return 'threat-badge critical'
  if (category === 'Warm Lead') return 'threat-badge medium'
  if (category === 'Interested') return 'threat-badge info'
  return 'threat-badge'
}

function topicText(lead) {
  const counts = lead?.engagement_analysis?.engaged_category_counts || {}
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1])
  if (!entries.length) return 'No engagement topics yet'
  return entries.map(([topic, count]) => `${topic}: ${count}`).join(' | ')
}

function SummaryLine({ icon: Icon, label, value }) {
  return (
    <div className="metric-card">
      <div className="metric-topline">
        <span>{label}</span>
        <Icon size={17} />
      </div>
      <div className="metric-value">{value}</div>
    </div>
  )
}

export default function CustomerIntelligenceWidget() {
  const [summary, setSummary] = useState(emptySummary)
  const [selectedLeadId, setSelectedLeadId] = useState('')
  const [loading, setLoading] = useState(true)
  const [apiOnline, setApiOnline] = useState(false)

  const fetchLeads = useCallback(async (signal) => {
    setLoading(true)
    try {
      const response = await fetch('/api/customer-intelligence/leads?limit=25', { signal })
      if (signal?.aborted) return
      if (response.ok) {
        const data = await response.json()
        if (signal?.aborted) return
        setSummary(data)
        setSelectedLeadId(current => current || data.leads?.[0]?.id || '')
        setApiOnline(true)
      } else {
        setApiOnline(false)
      }
    } catch (error) {
      if (error?.name === 'AbortError') return
      setApiOnline(false)
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetchLeads(controller.signal)
    const interval = setInterval(() => fetchLeads(controller.signal), 30000)
    return () => {
      controller.abort()
      clearInterval(interval)
    }
  }, [fetchLeads])

  const selectedLead = useMemo(
    () => summary.leads.find(lead => lead.id === selectedLeadId) || summary.leads[0],
    [selectedLeadId, summary.leads],
  )

  return (
    <div>
      <div className="section-header">
        <div>
          <h2>Client Opportunity Desk</h2>
          <div className="section-kicker">LinkedIn engagement converted into lead intent and follow-up actions.</div>
        </div>
        <div className="inline-group">
          <span className="status-pill">
            <span className={`status-dot ${apiOnline ? 'online' : 'offline'}`} />
            {apiOnline ? 'Lead API online' : 'Lead API offline'}
          </span>
          <button className="btn subtle icon-button" onClick={() => fetchLeads()} aria-label="Refresh lead queue">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      <div className="metrics-grid lead-summary-grid">
        <SummaryLine icon={Users} label="Leads" value={summary.total_leads} />
        <SummaryLine icon={Target} label="Hot" value={summary.hot_leads} />
        <SummaryLine icon={Target} label="Warm" value={summary.warm_leads} />
        <SummaryLine icon={Building2} label="Companies" value={summary.companies_identified} />
      </div>

      <div className="work-grid">
        <div className="panel">
          <div className="table-head lead-table-head">
            <span>Potential client</span>
            <span>Company</span>
            <span>Score</span>
            <span>Stage</span>
          </div>

          {loading && summary.leads.length === 0 ? (
            <div className="loading-state">Loading client opportunity queue.</div>
          ) : summary.leads.length === 0 ? (
            <div className="empty-state">
              No LinkedIn engagements have been analyzed. Ingest engagement data to identify client intent.
            </div>
          ) : summary.leads.map(lead => (
            <button
              key={lead.id}
              className={`lead-row${selectedLead?.id === lead.id ? ' selected' : ''}`}
              onClick={() => setSelectedLeadId(lead.id)}
              aria-pressed={selectedLead?.id === lead.id}
              aria-label={`Review ${lead.lead_profile.name}, intent score ${lead.intent_score}, ${lead.lead_category}`}
            >
              <span>
                <strong className="row-title">{lead.lead_profile.name}</strong>
                <span className="row-subtext">{lead.lead_profile.job_title || 'Unknown role'}</span>
              </span>
              <span className="row-subtext">{lead.lead_profile.company || 'Unknown company'}</span>
              <span className="threat-score">{lead.intent_score}</span>
              <span className={categoryClass(lead.lead_category)}>{lead.lead_category}</span>
            </button>
          ))}
        </div>

        <aside className="panel">
          <div className="panel-header">
            <div>
              <h2 style={{ fontSize: 15 }}>Next Best Action</h2>
              <div className="section-kicker">Context for the selected lead.</div>
            </div>
          </div>

          <div className="panel-body">
            {selectedLead ? (
              <div className="detail-stack">
                <div>
                  <div className="row-title">{selectedLead.lead_profile.name}</div>
                  <div className="row-subtext">
                    {selectedLead.lead_profile.role_category} at {selectedLead.lead_profile.company || 'unknown company'}
                  </div>
                </div>

                <div className="detail-block">
                  <div className="detail-label">Insights</div>
                  <ul className="insight-list">
                    {selectedLead.ai_insights.map(insight => <li key={insight}>{insight}</li>)}
                  </ul>
                </div>

                <div className="detail-block">
                  <div className="detail-label">Intel topics</div>
                  <div className="detail-value">{topicText(selectedLead)}</div>
                </div>

                <div className="detail-block">
                  <div className="detail-label">Recommended action</div>
                  <div className="detail-value">{selectedLead.recommended_action}</div>
                </div>
              </div>
            ) : (
              <div className="empty-state">Select a lead to review the recommended action.</div>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
