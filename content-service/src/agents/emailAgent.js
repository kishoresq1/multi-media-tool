import Anthropic from '@anthropic-ai/sdk';
import { parseJsonResponse } from './json.js';
import { plainText } from '../utils/safety.js';
import { makeLogger } from '../utils/logger.js';

const log = makeLogger('EmailAgent');

const EMAIL_SYSTEM = `You are a cybersecurity marketing expert for SQ1 Security.
Generate a professional email campaign from threat intelligence.
Return ONLY valid JSON with subject, preheader, headline, body, cta_text, recommended_action, tone, template_type.`;

function fallbackEmail(intel) {
  const title = intel?.title || 'Security Intelligence Update';
  const severity = intel?.severity || 'INFO';
  const tone = severity === 'CRITICAL' || intel?.classification === 'BREACH' ? 'urgent' : 'informative';
  return {
    subject: plainText(`${title} requires review`, 160),
    preheader: plainText(`${severity} ${intel?.classification || 'INTEL'} from SQ1 Security.`, 180),
    headline: plainText(title, 160),
    body: `<p>${intel?.summary || 'A new security intelligence item is ready for review.'}</p><p><strong>Recommended next step:</strong> Review exposure, prioritize remediation, and brief affected stakeholders.</p>`,
    cta_text: 'Review Exposure',
    recommended_action: 'Review exposure and prioritize remediation.',
    tone,
    template_type: mapTemplateType(intel?.classification)
  };
}

function normalizeEmailCampaign(value, fallback) {
  const campaign = { ...fallback, ...(value || {}) };
  return {
    subject: plainText(campaign.subject, 160),
    preheader: plainText(campaign.preheader, 180),
    headline: plainText(campaign.headline, 160),
    body: escapeCampaignBody(campaign.body),
    cta_text: plainText(campaign.cta_text, 60),
    recommended_action: plainText(campaign.recommended_action, 220),
    tone: ['urgent', 'informative', 'corrective', 'digest'].includes(campaign.tone)
      ? campaign.tone
      : fallback.tone,
    template_type: plainText(campaign.template_type, 40)
  };
}

function escapeCampaignBody(body = '') {
  return String(body)
    .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/<(\/?)(p|strong|em|br|ul|ol|li)\b[^>]*>/gi, '[[TAG:$1$2]]')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\[\[TAG:([/\w]+)\]\]/g, '<$1>');
}

function mapTemplateType(classification = '') {
  const key = classification.toUpperCase();
  if (key === 'BREACH') return 'breach';
  if (key === 'COMPLIANCE') return 'compliance';
  if (key === 'MISINFORMATION') return 'misinfo';
  if (key === 'VULNERABILITY') return 'vuln';
  return 'threat';
}

export async function generateEmail(intel) {
  log.info('Email campaign generation requested', { intelId: intel?.id, title: intel?.title, severity: intel?.severity, classification: intel?.classification });

  const fallback = fallbackEmail(intel);

  if (process.env.MARKETING_DISABLE_LLM === 'true') {
    log.info('LLM disabled (MARKETING_DISABLE_LLM=true) — using fallback email template');
    return normalizeEmailCampaign(fallback, fallback);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    log.warn('ANTHROPIC_API_KEY not set — using fallback email template');
    return normalizeEmailCampaign(fallback, fallback);
  }

  log.info('Calling Claude API for email campaign', { model: 'claude-sonnet-4-6' });
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1000,
      system: EMAIL_SYSTEM,
      messages: [
        {
          role: 'user',
          content: `Generate email for this intel:\nTitle: ${intel.title}\nClassification: ${intel.classification}\nSeverity: ${intel.severity}\nSummary: ${intel.summary}\nCVEs: ${(intel.cveIds || []).join(', ') || 'None'}`
        }
      ]
    });
    log.info('Claude API email generation succeeded');
    return normalizeEmailCampaign(parseJsonResponse(message.content?.[0]?.text, fallback), fallback);
  } catch (err) {
    log.error('Claude API email generation failed — using fallback', { error: err?.message });
    return normalizeEmailCampaign(fallback, fallback);
  }
}
