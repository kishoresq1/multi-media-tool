import { useEffect, useState } from 'react'
import EmployeeLeakTable from '../components/EmployeeLeakTable.jsx'

export default function Employees() {
  const [companies, setCompanies] = useState([])
  const [selected, setSelected] = useState(null)
  const [employees, setEmployees] = useState([])
  const [empLoading, setEmpLoading] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/companies', { signal: controller.signal })
      .then(r => r.ok ? r.json() : [])
      .then(data => { setCompanies(data); if (data.length) setSelected(data[0].id) })
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!selected) return
    const controller = new AbortController()
    setEmpLoading(true)
    fetch(`/api/employees/${selected}`, { signal: controller.signal })
      .then(r => r.ok ? r.json() : [])
      .then(data => { setEmployees(data); setEmpLoading(false) })
      .catch(error => {
        if (error?.name !== 'AbortError') setEmpLoading(false)
      })
    return () => controller.abort()
  }, [selected])

  return (
    <div>
      <div className="page-toolbar">
        <h2 className="page-title">People Exposure Monitor</h2>
        <label className="field">
          <span className="field-label">Client</span>
          <select
            className="input-control"
            value={selected || ''}
            onChange={e => setSelected(e.target.value)}
          >
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
      </div>

      <div className="surface-panel">
        <EmployeeLeakTable
          employees={employees}
          companyId={selected}
          loading={empLoading}
          onRefresh={() => {
            if (!selected) return
            fetch(`/api/employees/${selected}`)
              .then(r => r.ok ? r.json() : [])
              .then(setEmployees)
          }}
        />
      </div>
    </div>
  )
}
