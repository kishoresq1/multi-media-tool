import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageCircle,
  Shield,
  Bug,
  Building2,
  BookOpen,
  Tags,
  Clock,
  Layers,
  Scale,
  Database,
  Settings2,
  Plug,
  Palette,
  Activity,
  Megaphone,
} from 'lucide-react'

const allNav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/live', label: 'Live feed', icon: Activity },
  { to: '/sources', label: 'Sources list', icon: Database },
  { to: '/social', label: 'Social feeds', icon: MessageCircle },
  { to: '/advisories', label: 'Advisories', icon: Shield },
  { to: '/breaches', label: 'Company breaches', icon: Building2 },
  { to: '/compliance', label: 'Compliance', icon: Scale },
  { to: '/vulnerabilities', label: 'Vulnerabilities', icon: Bug },
  { to: '/blogs', label: 'Research blogs', icon: BookOpen },
  { to: '/unified', label: 'Unified intel', icon: Layers },
  { to: '/sources/configure', label: 'Source configuration', icon: Settings2 },
  { to: '/studio', label: 'Studio config', icon: Palette },
  { to: '/keywords', label: 'Keywords', icon: Tags },
  { to: '/jobs', label: 'Background jobs', icon: Clock },
  { to: '/integrations', label: 'Integrations', icon: Plug },
  { to: '/marketing', label: 'Marketing dashboard', icon: Megaphone },
]

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1 className="sidebar-title">Zero Day Radar</h1>
      </div>

      <nav className="sidebar-nav">
        {allNav.map(({ to, label: text, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end ?? false}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={17} strokeWidth={2} />
            {text}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
