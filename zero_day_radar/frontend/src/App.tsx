import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { SocialIntel } from './pages/SocialIntel'
import { Advisories } from './pages/Advisories'
import { Vulnerabilities } from './pages/Vulnerabilities'
import { Blogs } from './pages/Blogs'
import { Breaches } from './pages/Breaches'
import { UnifiedIntelPage } from './pages/UnifiedIntel'
import { Compliance } from './pages/Compliance'
import { Keywords } from './pages/Keywords'
import { Jobs } from './pages/Jobs'
import { ScoredPosts } from './pages/ScoredPosts'
import { SourcesList } from './pages/SourcesList'
import { SourceConfiguration } from './pages/SourceConfiguration'
import { ToolsIntegrations } from './pages/ToolsIntegrations'
import { StudioConfig } from './pages/StudioConfig'
import { LiveFeed } from './pages/LiveFeed'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="live" element={<LiveFeed />} />
          <Route path="social" element={<SocialIntel />} />
          <Route path="advisories" element={<Advisories />} />
          <Route path="vulnerabilities" element={<Vulnerabilities />} />
          <Route path="blogs" element={<Blogs />} />
          <Route path="breaches" element={<Breaches />} />
          <Route path="unified" element={<UnifiedIntelPage />} />
          <Route path="compliance" element={<Compliance />} />
          <Route path="keywords" element={<Keywords />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="scored" element={<ScoredPosts />} />
          <Route path="sources" element={<SourcesList />} />
          <Route path="sources/configure" element={<SourceConfiguration />} />
          <Route path="integrations" element={<ToolsIntegrations />} />
          <Route path="studio" element={<StudioConfig />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
