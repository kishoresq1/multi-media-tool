import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { listAlerts, sendAlert } from '../api/marketingApi.js';
import { IntelSummary } from './CampaignBuilder.jsx';
import { ActionPanelSkeleton, PayloadSkeleton } from './LoadingSkeleton.jsx';

export default function CommsPanel({ intel, onNotice }) {
  const [lastAlert, setLastAlert] = useState(null);
  const [alertLog, setAlertLog] = useState([]);
  const [channels, setChannels] = useState({ slackConfigured: false, teamsConfigured: false });
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void refreshAlerts(controller.signal);
    return () => controller.abort();
  }, []);

  async function refreshAlerts(signal) {
    setLoadingHistory(true);
    try {
      const result = await listAlerts({ signal }).catch(() => ({ alerts: [], channels }));
      if (signal?.aborted) return;
      setAlertLog(result.alerts || []);
      setChannels(result.channels || channels);
    } finally {
      if (!signal?.aborted) setLoadingHistory(false);
    }
  }

  async function send() {
    if (!intel) return;
    setLoading(true);
    try {
      const result = await sendAlert(intel);
      setLastAlert(result.results);
      await refreshAlerts();
      onNotice?.(
        result.results.slack.sent || result.results.teams.sent
          ? 'Security team alert sent.'
          : 'Alert payload prepared; configure webhooks to send.'
      );
    } catch {
      onNotice?.('Security team alert failed. Check webhook settings and retry.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel two-column">
      <div>
        <p className="eyebrow">Internal Comms</p>
        <h2>Security Team Alerts</h2>
        <IntelSummary intel={intel} />
        <button className="primary-action" onClick={send} disabled={!intel || loading}>
          <Bell size={16} />
          {loading ? 'Preparing alert' : 'Send Alert to Security Team'}
        </button>
      </div>
      <div className="preview-pane">
        <div className="status-line">
          <span className={channels.slackConfigured ? 'pulse' : 'pulse muted-pulse'} />
          Slack webhook {channels.slackConfigured ? 'configured' : 'not configured'}
        </div>
        <div className="status-line">
          <span className={channels.teamsConfigured ? 'pulse' : 'pulse muted-pulse'} />
          Teams webhook {channels.teamsConfigured ? 'configured' : 'not configured'}
        </div>
        <div className="alert-log">
          <p className="eyebrow">Last 5 Alerts</p>
          {loadingHistory ? (
            <ActionPanelSkeleton rows={3} labelWidth={86} />
          ) : alertLog.length === 0 ? (
            <div className="empty-state compact-empty">No alerts logged yet.</div>
          ) : (
            alertLog.map((alert) => (
              <div className="subscriber-row" key={alert.id}>
                <strong>{alert.severity} - {alert.classification}</strong>
                <span>{alert.title}</span>
              </div>
            ))
          )}
        </div>
        {loading ? (
          <PayloadSkeleton />
        ) : lastAlert ? (
          <pre className="payload-preview">{JSON.stringify(lastAlert, null, 2)}</pre>
        ) : (
          <div className="empty-state">Alert payload details appear after sending.</div>
        )}
      </div>
    </section>
  );
}
