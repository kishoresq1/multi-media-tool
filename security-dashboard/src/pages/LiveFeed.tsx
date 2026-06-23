import { useState, useEffect, useCallback } from 'react'
import { Activity, Shield, Bug, MessageCircle, Globe, Clock, Zap, ExternalLink, RefreshCw } from 'lucide-react'
import { PageHeader, Loading, ErrorBanner } from '../components/shared'
import { api } from '../api/client'

interface FeedItem {
  id: string
  type: 'vulnerability' | 'advisory' | 'social' | 'breach'
  title: string
  source: string
  timestamp: string
  url: string
  severity?: string
  rawDate: string
}

const FEED_TYPES = {
  vulnerability: { icon: Bug, color: 'var(--danger)', label: 'Vulnerability' },
  advisory: { icon: Shield, color: 'var(--warning)', label: 'Advisory' },
  social: { icon: MessageCircle, color: 'var(--info)', label: 'Social' },
  breach: { icon: Globe, color: 'var(--accent)', label: 'Breach' },
}

export function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetchRealData = useCallback(async () => {
    try {
      const [socialRes, advisoryRes, vulnRes, breachRes] = await Promise.all([
        api.socialPosts({ limit: 10 }),
        api.advisories({ limit: 10 }),
        api.vulnerabilities({ limit: 10 }),
        api.breaches({ limit: 10 }),
      ])

      const combined: FeedItem[] = [
        ...socialRes.posts.map(p => ({
          id: `social-${p.id}`,
          type: 'social' as const,
          title: p.title || p.content.slice(0, 100),
          source: p.source_name || p.platform,
          timestamp: new Date(p.published_at || p.created_at || '').toLocaleTimeString(),
          url: p.url || '#',
          severity: undefined,
          rawDate: p.published_at || p.created_at || '',
        })),
        ...advisoryRes.advisories.map(a => ({
          id: `advisory-${a.id}`,
          type: 'advisory' as const,
          title: a.title,
          source: a.source_name,
          timestamp: new Date(a.published_at || a.created_at || '').toLocaleTimeString(),
          url: a.url || '#',
          severity: a.severity || undefined,
          rawDate: a.published_at || a.created_at || '',
        })),
        ...vulnRes.items.map(v => ({
          id: `vuln-${v.id}`,
          type: 'vulnerability' as const,
          title: v.title,
          source: v.source_name,
          timestamp: new Date(v.published_at || v.created_at || '').toLocaleTimeString(),
          url: v.url || '#',
          severity: v.severity || undefined,
          rawDate: v.published_at || v.created_at || '',
        })),
        ...breachRes.items.map(b => ({
          id: `breach-${b.id}`,
          type: 'breach' as const,
          title: b.title,
          source: b.source_name,
          timestamp: new Date(b.published_at || b.created_at || '').toLocaleTimeString(),
          url: b.url || '#',
          severity: b.risk_level || undefined,
          rawDate: b.published_at || b.created_at || '',
        })),
      ]

      // Sort by date descending
      combined.sort((a, b) => new Date(b.rawDate).getTime() - new Date(a.rawDate).getTime())
      
      setItems(combined.slice(0, 50))
      setError(null)
    } catch (err) {
      console.error('Failed to fetch live feed data:', err)
      setError('Failed to connect to real-time intelligence stream.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRealData()
    
    const interval = setInterval(() => {
      if (!isPaused) {
        fetchRealData()
      }
    }, 15000) // Refresh every 15 seconds for real data

    return () => clearInterval(interval)
  }, [isPaused, fetchRealData])

  if (loading && items.length === 0) return <Loading text="Connecting to intelligence stream…" />

  return (
    <>
      <PageHeader 
        title="Live Intelligence Feed" 
        description="Real-time stream of security events, vulnerabilities, and social intelligence fetched directly from backend collectors."
        actions={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setLoading(true)
                fetchRealData()
              }}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              Refresh
            </button>
            <button 
              className={`btn ${isPaused ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setIsPaused(!isPaused)}
            >
              {isPaused ? <Zap size={14} /> : <Clock size={14} />}
              {isPaused ? 'Resume Feed' : 'Pause Feed'}
            </button>
          </div>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="panel" style={{ marginTop: '1rem', height: 'calc(100vh - 250px)' }}>
        <div className="panel-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} className={isPaused ? '' : 'text-primary pulsing'} />
            <h3>Live Activity</h3>
            {!isPaused && <span className="status-dot ok" style={{ marginLeft: '0.5rem' }}></span>}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Showing {items.length} real-time events
          </div>
        </div>
        
        <div 
          className="panel-body" 
          style={{ 
            overflowY: 'auto', 
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
          }}
        >
          {items.map((item) => {
            const Config = FEED_TYPES[item.type]
            return (
              <div 
                key={item.id} 
                className="card" 
                style={{ 
                  padding: '1rem', 
                  display: 'flex', 
                  gap: '1rem', 
                  alignItems: 'flex-start',
                  animation: 'slideIn 0.3s ease-out',
                  borderLeft: `4px solid ${Config.color}`,
                  position: 'relative'
                }}
              >
                <div 
                  style={{ 
                    background: `${Config.color}15`, 
                    color: Config.color,
                    padding: '0.5rem',
                    borderRadius: '8px',
                    display: 'flex'
                  }}
                >
                  <Config.icon size={20} />
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: Config.color }}>
                      {Config.label}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={12} /> {item.timestamp}
                    </span>
                  </div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: 600 }}>
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="feed-link"
                      style={{ color: 'inherit', textDecoration: 'none' }}
                    >
                      {item.title}
                    </a>
                  </h4>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>{item.source}</span>
                    {item.severity && (
                      <span className={`badge badge-${item.severity.toLowerCase().includes('crit') || item.severity.toLowerCase().includes('high') ? 'danger' : 'warning'}`} style={{ fontSize: '0.7rem' }}>
                        {item.severity}
                      </span>
                    )}
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ marginLeft: 'auto', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                    >
                      View Source <ExternalLink size={12} />
                    </a>
                  </div>
                </div>
              </div>
            )
          })}
          {items.length === 0 && !loading && (
            <div className="empty-state">
              <p>No real-time intelligence detected yet.</p>
              <p style={{ fontSize: '0.85rem' }}>Make sure backend collectors are running.</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        .pulsing {
          animation: pulse 2s infinite ease-in-out;
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .feed-link:hover {
          color: var(--accent) !important;
          text-decoration: underline !important;
        }
      `}</style>
    </>
  )
}
