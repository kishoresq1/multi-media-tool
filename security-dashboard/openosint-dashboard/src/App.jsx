import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { Building2, LayoutDashboard, Users } from 'lucide-react'
import Home from './pages/Home.jsx'
import Companies from './pages/Companies.jsx'
import CompanyDetail from './pages/CompanyDetail.jsx'
import Employees from './pages/Employees.jsx'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Operations', exact: true },
  { to: '/companies', icon: Building2, label: 'Clients' },
  { to: '/employees', icon: Users, label: 'People Exposure' },
]

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-lockup">
        <div className="brand-name">Catapult</div>
        <div className="brand-subtitle">Client intelligence operations</div>
      </div>

      <nav className="nav-list" aria-label="Primary navigation">
        {NAV.map(({ to, icon: Icon, label, exact }) => (
          <NavLink key={to} to={to} end={exact} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <Icon size={17} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div>Operational build</div>
        <div>Threat monitoring, client response, and asset handoff.</div>
      </div>
    </aside>
  )
}

function Layout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-panel">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:id" element={<CompanyDetail />} />
          <Route path="/employees" element={<Employees />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
