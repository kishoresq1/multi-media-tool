import { randomUUID } from 'node:crypto';
import { sendSlackAlert, sendTeamsAlert } from '../../agents/slackTeamsAgent.js';
import { persist } from '../db.js';

export default function commsRoutes(db) {
  async function alert(req, res) {
    const intel = req.body?.intel;
    if (!intel?.title || !intel?.classification || !intel?.severity) {
      return res.status(400).json({ error: 'intel title, classification, and severity are required' });
    }

    const [slack, teams] = await Promise.all([sendSlackAlert(intel), sendTeamsAlert(intel)]);
    const record = {
      id: randomUUID(),
      intelId: intel.id || null,
      title: intel.title,
      severity: intel.severity,
      classification: intel.classification,
      createdAt: new Date().toISOString(),
      results: { slack, teams }
    };
    db.data.alerts.push(record);
    await persist(db);
    return res.json({ results: { slack, teams }, alert: record });
  }

  function list(_req, res) {
    return res.json({
      channels: {
        slackConfigured: Boolean(process.env.SLACK_WEBHOOK_URL),
        teamsConfigured: Boolean(process.env.TEAMS_WEBHOOK_URL)
      },
      alerts: db.data.alerts.slice(-5).reverse()
    });
  }

  return { alert, list };
}
