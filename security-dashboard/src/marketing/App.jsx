import { lazy, Suspense, useEffect, useState } from 'react';
import {
  Activity,
  Bell,
  Clapperboard,
  Image,
  LayoutDashboard,
  Mail,
  Radio,
  Users
} from 'lucide-react';
import MarketingDashboard from './components/MarketingDashboard.jsx';
import { getIntel, listAssets, listCampaigns, listSubscribers } from './api/marketingApi.js';

const CampaignBuilder = lazy(() => import('./components/CampaignBuilder.jsx'));
const HyperFrameStudio = lazy(() => import('./components/HyperFrameStudio.jsx'));
const VideoBuilder = lazy(() => import('./components/VideoBuilder.jsx'));
const SubscribePortal = lazy(() => import('./components/SubscribePortal.jsx'));
const CommsPanel = lazy(() => import('./components/CommsPanel.jsx'));
const AssetGallery = lazy(() => import('./components/AssetGallery.jsx'));

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'visuals', label: 'Visuals', icon: Image },
  { id: 'campaigns', label: 'Campaigns', icon: Mail },
  { id: 'videos', label: 'Videos', icon: Clapperboard },
  { id: 'subscribers', label: 'Subscribers', icon: Users },
  { id: 'comms', label: 'Comms', icon: Bell },
  { id: 'gallery', label: 'Gallery', icon: Activity }
];

export default function App() {
  const [tab, setTab] = useState(() =>
    window.location.pathname === '/marketing/subscribe' ? 'subscribers' : 'dashboard'
  );
  const [intelItems, setIntelItems] = useState([]);
  const [feedSource, setFeedSource] = useState('mock');
  const [selectedIntel, setSelectedIntel] = useState(null);
  const [activeTool, setActiveTool] = useState(null);
  const [subscribers, setSubscribers] = useState([]);
  const [assets, setAssets] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    refreshData(controller.signal);
    const timer = setInterval(() => refreshIntel(controller.signal), 30000);
    const onPopState = () => {
      setTab(window.location.pathname === '/marketing/subscribe' ? 'subscribers' : 'dashboard');
    };
    window.addEventListener('popstate', onPopState);
    return () => {
      controller.abort();
      clearInterval(timer);
      window.removeEventListener('popstate', onPopState);
    };
  }, []);

  function switchTab(nextTab) {
    setTab(nextTab);
    const path = nextTab === 'subscribers' ? '/marketing/subscribe' : '/marketing';
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
  }

  async function refreshIntel(signal) {
    const result = await getIntel({ signal });
    if (signal?.aborted) return;
    setIntelItems(result.items || []);
    setFeedSource(result.source === 'live' ? 'live' : result.source === 'mock' ? 'mock' : 'portal');
  }

  async function refreshData(signal) {
    setLoading(true);
    try {
      await refreshIntel(signal);
      const [subscriberResult, assetResult, campaignResult] = await Promise.all([
        listSubscribers({ signal }).catch(() => ({ subscribers: [] })),
        listAssets({ signal }).catch(() => ({ assets: [] })),
        listCampaigns({ signal }).catch(() => ({ campaigns: [] }))
      ]);
      if (signal?.aborted) return;
      setSubscribers(subscriberResult.subscribers || []);
      setAssets(assetResult.assets || []);
      setCampaigns(campaignResult.campaigns || []);
    } catch (error) {
      if (error?.name !== 'AbortError') setFeedSource('mock');
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }

  function openTool(tool, intel) {
    setSelectedIntel(intel);
    setActiveTool(tool);
    switchTab(tool === 'email' ? 'campaigns' : tool === 'video' ? 'videos' : tool === 'alert' ? 'comms' : 'visuals');
  }

  function handleAssetCreated(asset) {
    setAssets((current) => [asset, ...current.filter((item) => item.id !== asset.id)]);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Radio size={24} />
          <div>
            <strong>Catapult</strong>
            <span>Marketing Intel</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="Marketing sections">
          {TABS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={tab === item.id ? 'nav-item active' : 'nav-item'}
                onClick={() => switchTab(item.id)}
                aria-pressed={tab === item.id}
              >
                <Icon size={17} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Catapult OSINT Pipeline</p>
            <h1>Marketing Intelligence Console</h1>
          </div>
          <div className={`feed-status ${feedSource}`}>
            <span className="pulse" />
              {feedSource === 'live'
                ? 'SQ1 portal queue'
                : feedSource === 'mock'
                  ? 'Mock intel feed'
                  : 'Awaiting portal push'}
          </div>
        </header>

        {notice && <div className="notice" role="status">{notice}</div>}

        <Suspense fallback={<div className="panel empty-state">Loading workspace.</div>}>
          {tab === 'dashboard' && (
            <MarketingDashboard
              intelItems={intelItems}
              subscribers={subscribers}
              assets={assets}
              campaigns={campaigns}
              loading={loading}
              feedSource={feedSource}
              onOpenTool={openTool}
              onNotice={setNotice}
            />
          )}
          {tab === 'campaigns' && <CampaignBuilder intel={selectedIntel} subscribers={subscribers} />}
          {tab === 'visuals' && (
            <HyperFrameStudio intel={selectedIntel} onAssetCreated={handleAssetCreated} />
          )}
          {tab === 'videos' && <VideoBuilder intel={selectedIntel} onAssetCreated={handleAssetCreated} />}
          {tab === 'subscribers' && (
            <SubscribePortal subscribers={subscribers} onSubscriberAdded={() => refreshData()} />
          )}
          {tab === 'comms' && (
            <CommsPanel intel={selectedIntel} onNotice={setNotice} activeTool={activeTool} />
          )}
          {tab === 'gallery' && <AssetGallery assets={assets} campaigns={campaigns} onRefresh={() => refreshData()} />}
        </Suspense>
      </main>
    </div>
  );
}
