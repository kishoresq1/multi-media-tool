import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import CompanyList from '../components/CompanyList.jsx'

export default function Companies() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', domain: '', contactEmail: '' })
  const [adding, setAdding] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const res = await fetch('/api/companies')
      if (res.ok) setCompanies(await res.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleAdd(e) {
    e.preventDefault()
    if (!form.name || !form.domain) return
    setAdding(true)
    try {
      const res = await fetch('/api/companies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (res.ok) {
        setForm({ name: '', domain: '', contactEmail: '' })
        setShowAdd(false)
        await load()
      }
    } finally {
      setAdding(false)
    }
  }

  return (
    <div>
      <div className="page-toolbar">
        <h2 className="page-title">Client Portfolio</h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="btn primary"
          aria-expanded={showAdd}
        >
          <Plus size={15} /> Add client
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="form-card">
          {[['Company Name', 'name', 'Acme Corp'], ['Domain', 'domain', 'acme.com'], ['Contact Email', 'contactEmail', 'admin@acme.com']].map(([label, key, ph]) => (
            <label key={key} className="field">
              <span className="field-label">{label}</span>
              <input
                className="input-control"
                value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                placeholder={ph}
              />
            </label>
          ))}
          <button type="submit" disabled={adding} className="btn subtle">
            {adding ? 'Adding client' : 'Add client'}
          </button>
        </form>
      )}

      <CompanyList companies={companies} loading={loading} />
    </div>
  )
}
