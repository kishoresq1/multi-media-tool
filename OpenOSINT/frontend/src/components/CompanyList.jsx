import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, Shield, Users, Globe } from 'lucide-react'

function riskClass(score = 0) {
  if (score >= 80) return 'risk-high'
  if (score >= 60) return 'risk-elevated'
  if (score >= 40) return 'risk-watch'
  return 'risk-clear'
}

function ThreatGauge({ score }) {
  const risk = riskClass(score)
  return (
    <div className={`gauge ${risk}`}>
      <div className="gauge-track" aria-hidden="true">
        <div className="gauge-bar" style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
      </div>
      <span className="risk-text" aria-label={`Threat score ${score}`}>{score}</span>
    </div>
  )
}

function timeAgo(iso) {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const h = Math.floor(diff / 3600000)
  if (h < 1) return 'Just now'
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function CompanyCard({ company }) {
  const navigate = useNavigate()
  const [scanning, setScanning] = useState(false)

  async function handleScan(e) {
    e.stopPropagation()
    if (scanning) return
    setScanning(true)
    try {
      await fetch(`/api/companies/${company.id}/scan`, { method: 'POST' })
    } finally {
      setScanning(false)
    }
  }

  function openCompany() {
    navigate(`/companies/${company.id}`)
  }

  function handleCardKeyDown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      openCompany()
    }
  }

  return (
    <div
      className="company-card"
      role="button"
      tabIndex={0}
      onClick={openCompany}
      onKeyDown={handleCardKeyDown}
      aria-label={`Open ${company.name} client detail`}
    >
      <div className="company-header">
        <div>
          <div className="row-title">{company.name}</div>
          <div className="company-meta">
            <Globe size={11} /> {company.domain}
          </div>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="btn subtle"
          aria-label={`Run OSINT scan for ${company.name}`}
        >
          <RefreshCw size={14} />
          {scanning ? 'Scanning' : 'Scan'}
        </button>
      </div>

      <div>
        <div className="detail-label">Threat score</div>
        <ThreatGauge score={company.threatScore || 0} />
      </div>

      <div className="company-meta">
        <span className="inline-group">
          <Users size={11} /> {company.employeeCount || 0} employees
        </span>
        <span>Last scan: {timeAgo(company.lastScan)}</span>
      </div>

      {company.tags?.length > 0 && (
        <div className="tag-list">
          {company.tags.map(tag => (
            <span key={tag} className="tag-chip">{tag}</span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function CompanyList({ companies = [], loading = false }) {
  if (loading) return (
    <div className="loading-state">Loading client portfolio.</div>
  )
  if (!companies.length) return (
    <div className="empty-state">No clients are being monitored yet. Add a client to start exposure tracking.</div>
  )
  return (
    <div className="company-grid">
      {companies.map(c => <CompanyCard key={c.id} company={c} />)}
    </div>
  )
}
