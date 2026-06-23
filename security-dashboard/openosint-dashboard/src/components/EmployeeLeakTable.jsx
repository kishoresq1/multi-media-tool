import { useState } from 'react'
import { Search } from 'lucide-react'

function riskClass({ breachCount = 0, pasteCount = 0 }) {
  if (breachCount >= 3 || pasteCount >= 2) return 'risk-high'
  if (breachCount >= 1 || pasteCount >= 1) return 'risk-elevated'
  return 'risk-clear'
}

function SeverityDot({ breachCount, pasteCount }) {
  const risk = riskClass({ breachCount, pasteCount })
  const label = risk === 'risk-high' ? 'High risk' : risk === 'risk-elevated' ? 'At risk' : 'Clear'
  return (
    <span className={`status-text ${risk}`}>
      <span className="status-marker" aria-hidden="true" />
      {label}
    </span>
  )
}

export default function EmployeeLeakTable({ employees = [], companyId, loading = false, onRefresh }) {
  const [scanning, setScanning] = useState(null)

  async function scanEmail(email) {
    setScanning(email)
    try {
      await fetch('/api/employees/scan-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      onRefresh?.()
    } finally {
      setScanning(null)
    }
  }

  if (loading) return <div className="loading-state">Loading employee exposure data.</div>
  if (!employees.length) return <div className="empty-state">No employees are linked to this client yet.</div>

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {['Employee', 'Email', 'Role', 'Risk', 'Breaches', 'Pastes', 'Services', ''].map(h => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {employees.map(emp => (
            <tr key={emp.email}>
              <td><strong>{emp.name}</strong></td>
              <td className="company-domain">{emp.email}</td>
              <td className="row-subtext">{emp.role}</td>
              <td><SeverityDot breachCount={emp.breachCount || 0} pasteCount={emp.pasteCount || 0} /></td>
              <td className={`risk-text ${(emp.breachCount || 0) > 0 ? 'risk-high' : 'risk-clear'}`}>
                {emp.breachCount || 0}
              </td>
              <td className={`risk-text ${(emp.pasteCount || 0) > 0 ? 'risk-elevated' : 'risk-clear'}`}>
                {emp.pasteCount || 0}
              </td>
              <td>
                <div className="tag-list">
                  {(emp.servicesFound || []).map(s => (
                    <span key={s} className="tag-chip">{s}</span>
                  ))}
                </div>
              </td>
              <td>
                <button
                  onClick={() => scanEmail(emp.email)}
                  disabled={scanning === emp.email}
                  className="btn subtle"
                  aria-label={`Scan exposure for ${emp.email}`}
                >
                  <Search size={14} />
                  {scanning === emp.email ? 'Scanning' : 'Scan'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
