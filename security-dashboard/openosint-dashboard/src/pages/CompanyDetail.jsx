import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import CompanyDrilldown from '../components/CompanyDrilldown.jsx'

export default function CompanyDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const controller = new AbortController()
    fetch(`/api/companies/${id}`, { signal: controller.signal })
      .then(r => r.ok ? r.json() : null)
      .then(data => { setCompany(data); setLoading(false) })
      .catch(error => {
        if (error?.name !== 'AbortError') setLoading(false)
      })
    return () => controller.abort()
  }, [id])

  if (loading) return <div className="loading-state">Loading client profile.</div>
  if (!company) return <div className="soft-error">Client not found.</div>

  return (
    <div>
      <button
        onClick={() => navigate('/companies')}
        className="btn link-button"
      >
        <ArrowLeft size={14} /> Back to clients
      </button>
      <CompanyDrilldown company={company} />
    </div>
  )
}
