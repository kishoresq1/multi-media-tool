import axios from 'axios';
import { plainText } from '../utils/safety.js';

const SEVERITY_EMOJI = {
  CRITICAL: ':red_circle:',
  HIGH: ':large_orange_circle:',
  MEDIUM: ':large_yellow_circle:',
  LOW: ':large_blue_circle:',
  INFO: ':white_circle:'
};

const SEVERITY_COLOR = {
  CRITICAL: 'FF0000',
  HIGH: 'FF6600',
  MEDIUM: 'FFCC00',
  LOW: '00D4FF',
  INFO: '888888'
};

export async function sendSlackAlert(intel) {
  const emoji = SEVERITY_EMOJI[intel.severity] || ':white_circle:';
  const title = plainText(intel.title, 220);
  const summary = plainText(intel.summary, 900);
  const classification = plainText(intel.classification, 60);
  const severity = plainText(intel.severity, 40);
  const payload = {
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: `${emoji} SQ1 OSINT: ${classification} Alert`
        }
      },
      {
        type: 'section',
        text: { type: 'mrkdwn', text: `*${title}*\n${summary}` }
      },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Severity:*\n${severity}` },
          { type: 'mrkdwn', text: `*Type:*\n${classification}` },
          { type: 'mrkdwn', text: `*CVEs:*\n${(intel.cveIds || []).map((cve) => plainText(cve, 40)).join(', ') || 'N/A'}` },
          { type: 'mrkdwn', text: `*Source Verified:*\n${intel.sourceVerified ? 'Yes' : 'No'}` }
        ]
      },
      { type: 'divider' },
      {
        type: 'context',
        elements: [{ type: 'mrkdwn', text: `SQ1 OSINT Platform - ${new Date().toUTCString()}` }]
      }
    ]
  };

  if (process.env.SLACK_WEBHOOK_URL) {
    try {
      await axios.post(process.env.SLACK_WEBHOOK_URL, payload);
      return { platform: 'slack', sent: true, payload };
    } catch (error) {
      return {
        platform: 'slack',
        sent: false,
        error: error?.message || 'Slack webhook failed',
        payload
      };
    }
  }
  return { platform: 'slack', sent: false, payload };
}

export async function sendTeamsAlert(intel) {
  const title = plainText(intel.title, 220);
  const summary = plainText(intel.summary, 900);
  const classification = plainText(intel.classification, 60);
  const severity = plainText(intel.severity, 40);
  const payload = {
    '@type': 'MessageCard',
    '@context': 'http://schema.org/extensions',
    themeColor: SEVERITY_COLOR[intel.severity] || '888888',
    summary: `SQ1 Alert: ${title}`,
    sections: [
      {
        activityTitle: `SQ1 OSINT - ${classification} Alert`,
        activitySubtitle: title,
        facts: [
          { name: 'Severity', value: severity },
          { name: 'Classification', value: classification },
          { name: 'CVEs', value: (intel.cveIds || []).map((cve) => plainText(cve, 40)).join(', ') || 'None' },
          { name: 'Source Verified', value: intel.sourceVerified ? 'Yes' : 'No' }
        ],
        text: summary
      }
    ]
  };

  if (process.env.TEAMS_WEBHOOK_URL) {
    try {
      await axios.post(process.env.TEAMS_WEBHOOK_URL, payload);
      return { platform: 'teams', sent: true, payload };
    } catch (error) {
      return {
        platform: 'teams',
        sent: false,
        error: error?.message || 'Teams webhook failed',
        payload
      };
    }
  }
  return { platform: 'teams', sent: false, payload };
}
