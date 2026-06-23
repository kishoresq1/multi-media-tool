import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'

const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/social': 'Social Feeds',
  '/advisories': 'Vendor Advisories',
  '/breaches': 'Company Breaches',
  '/unified': 'Unified Intelligence',
  '/compliance': 'Compliance Intelligence',
  '/vulnerabilities': 'Vulnerabilities',
  '/blogs': 'Research Blogs',
  '/keywords': 'Keywords',
  '/jobs': 'Background Jobs',
  '/scored': 'Scored Posts',
  '/sources': 'Sources',
  '/sources/configure': 'Source Configuration',
  '/integrations': 'Tools & Integrations',
  '/marketing': 'Marketing Dashboard',
}

export function Layout() {
  const { pathname } = useLocation()
  const title = TITLES[pathname] ?? (pathname.startsWith('/marketing') ? 'Marketing Dashboard' : 'Unified Multimedia Platform')

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main">
        <header className="topbar">
          <h1 className="topbar-title">{title}</h1>
          <div className="topbar-actions">
            <span className="badge badge-neutral">Live monitor</span>
          </div>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
