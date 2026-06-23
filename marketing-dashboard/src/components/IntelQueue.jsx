import { Bell, Clapperboard, Image, Mail, Users } from 'lucide-react';
import { sendAlert } from '../api/marketingApi.js';
import { countMatchedSubscribers } from '../utils/subscriberMatching.js';

const SEVERITY_CLASS = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info'
};

export default function IntelQueue({ items, subscribers = [], loading, feedSource, onOpenTool, onNotice }) {
  async function alertTeam(item) {
    try {
      const response = await sendAlert(item);
      onNotice?.(
        response.results?.slack?.sent || response.results?.teams?.sent
          ? 'Alert sent to configured channels.'
          : 'Alert payload prepared; configure webhooks to send.'
      );
      onOpenTool?.('alert', item);
    } catch {
      onNotice?.('Alert preparation failed. Open Comms to retry.');
    }
  }

  if (loading) {
    return <div className="panel empty-state">Loading intel queue.</div>;
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Intel Queue</p>
          <h2>Ready To Market</h2>
        </div>
        <span className="source-chip">
          {feedSource === 'live' ? 'SQ1 Portal' : feedSource === 'mock' ? 'Mock feed' : 'Portal gated'}
        </span>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">No intel items waiting for marketing.</div>
      ) : (
        <div className="queue-list">
          {items.map((item) => {
            const matchedSubscriberCount = countMatchedSubscribers(item, subscribers);

            return (
              <article className={`intel-card ${SEVERITY_CLASS[item.severity] || 'info'}`} key={item.id}>
                <div className="intel-header">
                  <div>
                    <div className="badge-row">
                      <span className={`severity ${SEVERITY_CLASS[item.severity] || 'info'}`}>
                        {item.severity}
                      </span>
                      <span className="classification">{item.classification}</span>
                      {item.sourceVerified && <span className="verified">Verified</span>}
                    </div>
                    <h3>{item.title}</h3>
                  </div>
                  <time>{formatTime(item.timestamp)}</time>
                </div>
                <p>{item.summary}</p>
                <div className="tag-row">
                  {(item.cveIds || []).map((cve) => (
                    <span className="cve" key={cve}>
                      {cve}
                    </span>
                  ))}
                  {(item.tags || []).slice(0, 4).map((tag) => (
                    <span className="tag" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="tag-row">
                  <Users size={15} />
                  <span className="classification">
                    {matchedSubscriberCount} matched subscriber
                    {matchedSubscriberCount === 1 ? '' : 's'}
                  </span>
                </div>
                <div className="action-row">
                  <button onClick={() => onOpenTool('email', item)} aria-label={`Create email campaign for ${item.title}`}>
                    <Mail size={15} />
                    Email Campaign
                  </button>
                  <button onClick={() => onOpenTool('visual', item)} aria-label={`Create visual asset for ${item.title}`}>
                    <Image size={15} />
                    Create Visual
                  </button>
                  <button onClick={() => onOpenTool('video', item)} aria-label={`Create video for ${item.title}`}>
                    <Clapperboard size={15} />
                    5s Visual
                  </button>
                  <button onClick={() => alertTeam(item)} aria-label={`Prepare team alert for ${item.title}`}>
                    <Bell size={15} />
                    Alert Team
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function formatTime(value) {
  if (!value) return 'now';
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(
    new Date(value)
  );
}
