import { useState } from 'react'
import { Check, Link2 } from 'lucide-react'

interface Integration {
  id: string
  name: string
  description: string
  iconClass: string
  letter: string
  envKeys: string[]
  status: 'connected' | 'optional' | 'planned'
}

const INTEGRATIONS: Integration[] = [
  {
    id: 'twitter',
    name: 'Twitter / X (Nitter)',
    description: 'Search X posts via Nitter RSS — no Twitter API key. Configure Nitter instances in backend .env.',
    iconClass: 'twitter',
    letter: '𝕏',
    envKeys: ['ZDR_NITTER_INSTANCES', 'ZDR_NITTER_VERIFY_SSL'],
    status: 'optional',
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    description: 'Discover public LinkedIn posts about vulnerabilities via search-engine scraping.',
    iconClass: 'linkedin',
    letter: 'in',
    envKeys: [],
    status: 'connected',
  },
  {
    id: 'instagram',
    name: 'Instagram',
    description: 'Monitor security researcher accounts and security hashtags. Requires Meta Graph API token.',
    iconClass: 'instagram',
    letter: 'IG',
    envKeys: ['ZDR_INSTAGRAM_ACCESS_TOKEN'],
    status: 'planned',
  },
  {
    id: 'teams',
    name: 'Microsoft Teams',
    description: 'Send high-confidence alerts to a Teams channel via incoming webhook.',
    iconClass: 'teams',
    letter: 'T',
    envKeys: ['ZDR_TEAMS_WEBHOOK_URL'],
    status: 'planned',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Push CVE and KEV alerts to Slack channels using an incoming webhook or bot token.',
    iconClass: 'slack',
    letter: 'S',
    envKeys: ['ZDR_SLACK_WEBHOOK_URL', 'ZDR_SLACK_BOT_TOKEN'],
    status: 'planned',
  },
  {
    id: 'mail',
    name: 'Email',
    description: 'Daily digest and critical-alert emails via SMTP or SendGrid.',
    iconClass: 'mail',
    letter: '@',
    envKeys: ['ZDR_SMTP_HOST', 'ZDR_SMTP_USER', 'ZDR_ALERT_EMAIL_TO'],
    status: 'planned',
  },
]

export function ToolsIntegrations() {
  const [connected, setConnected] = useState<Record<string, boolean>>({})

  const statusBadge = (status: Integration['status']) => {
    if (status === 'connected') return <span className="badge badge-success">Active</span>
    if (status === 'optional') return <span className="badge badge-warning">Configure</span>
    return <span className="badge badge-neutral">Coming soon</span>
  }

  return (
    <>
      <div className="page-header">
        <h2>Tools & integrations</h2>
        <p>Connect social platforms and notification channels. Backend collectors run automatically every 20 minutes via Celery.</p>
      </div>

      <div className="integration-grid">
        {INTEGRATIONS.map((item) => (
          <article key={item.id} id={item.id} className="integration-card">
            <div className="integration-card-header">
              <div className={`integration-icon ${item.iconClass}`}>{item.letter}</div>
              <div>
                <h4>{item.name}</h4>
                {statusBadge(item.status)}
              </div>
            </div>
            <p>{item.description}</p>
            {item.envKeys.length > 0 && (
              <div>
                <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: 6 }}>
                  Environment variables
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {item.envKeys.map((k) => (
                    <code key={k} className="mono" style={{ fontSize: '0.7rem', background: 'var(--bg)', padding: '2px 6px', borderRadius: 4, border: '1px solid var(--border)' }}>
                      {k}
                    </code>
                  ))}
                </div>
              </div>
            )}
            <div style={{ marginTop: 'auto', display: 'flex', gap: '0.5rem' }}>
              {item.status !== 'planned' ? (
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setConnected((c) => ({ ...c, [item.id]: !c[item.id] }))}
                >
                  {connected[item.id] ? <Check size={14} /> : <Link2 size={14} />}
                  {connected[item.id] ? 'Connected' : 'Connect'}
                </button>
              ) : (
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} disabled>
                  Notify me
                </button>
              )}
            </div>
          </article>
        ))}
      </div>

      <section className="config-section" style={{ marginTop: '1.5rem' }}>
        <h3>Also integrated in backend</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          These run without extra UI setup — data appears on the Dashboard automatically.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {['Reddit', 'Hacker News', 'CVE Program', 'NVD', 'CISA KEV', 'GitHub PoC', 'Exploit-DB', 'Metasploit', 'Vendor advisories', 'Research blogs'].map((t) => (
            <span key={t} className="badge badge-success">{t}</span>
          ))}
        </div>
      </section>
    </>
  )
}
