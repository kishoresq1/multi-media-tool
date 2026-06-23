import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import EmployeeLeakTable from './EmployeeLeakTable.jsx'

const TABS = ['Employees', 'WHOIS/Report', 'Intel Feed']

export default function CompanyDrilldown({ company }) {
  const [tab, setTab] = useState('Employees')
  const [employees, setEmployees] = useState([])
  const [empLoading, setEmpLoading] = useState(true)
  const [scanResult, setScanResult] = useState(null)
  const [scanning, setScanning] = useState(false)

  async function loadEmployees(signal) {
    setEmpLoading(true)
    try {
      const res = await fetch(`/api/employees/${company.id}`, { signal })
      if (signal?.aborted) return
      if (res.ok) setEmployees(await res.json())
    } catch (error) {
      if (error?.name !== 'AbortError') setEmployees([])
    } finally {
      if (!signal?.aborted) setEmpLoading(false)
    }
  }

  async function triggerScan() {
    if (scanning) return
    setScanning(true)
    try {
      const res = await fetch(`/api/companies/${company.id}/scan`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setScanResult(data.report)
        setTab('WHOIS/Report')
      }
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    loadEmployees(controller.signal)
    return () => controller.abort()
  }, [company.id])

  function riskClass(score = 0) {
    if (score >= 80) return 'risk-high'
    if (score >= 60) return 'risk-elevated'
    if (score >= 40) return 'risk-watch'
    return 'risk-clear'
  }

  return (
    <div>
      <div className="page-toolbar">
        <div>
          <h2 className="page-title">{company.name}</h2>
          <div className="company-domain">{company.domain}</div>
        </div>
        <div className="inline-group">
          <div>
            <div className="detail-label">Threat score</div>
            <div className={`metric-value ${riskClass(company.threatScore || 0)}`}>
              {company.threatScore || 0}
            </div>
          </div>
          <button
            onClick={triggerScan}
            disabled={scanning}
            className="btn primary"
            aria-label={`Run full OSINT scan for ${company.name}`}
          >
            <RefreshCw size={15} />
            {scanning ? 'Scanning' : 'Full OSINT Scan'}
          </button>
        </div>
      </div>

      <div className="tabs" role="tablist" aria-label="Company detail sections">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`tab-button${tab === t ? ' active' : ''}`}
            role="tab"
            aria-selected={tab === t}
          >{t}</button>
        ))}
      </div>

      {tab === 'Employees' && (
        <EmployeeLeakTable
          employees={employees}
          companyId={company.id}
          loading={empLoading}
          onRefresh={loadEmployees}
        />
      )}

      {tab === 'WHOIS/Report' && (
        <div className="report-block">
          {scanResult || 'No scan data yet. Run Full OSINT Scan to collect a fresh report.'}
        </div>
      )}

      {tab === 'Intel Feed' && (
        <div className="empty-state compact-empty">
          Intel filtering by company coming soon.
        </div>
      )}
    </div>
  )
}
